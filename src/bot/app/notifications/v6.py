"""V6 topic-targeted notification dispatch.

Where V5 broadcasts one message per platform and lets the device filter, V6
sends one message per *audience class* with an FCM condition naming the
launch's own attributes. A device subscribes to the type topics of exactly one
class, so at most one condition can match it -- duplicate delivery is
impossible by construction rather than by deduplication.

Payloads and APNs/Android config are identical to V5 on purpose: during the
dual-send window one payload shape ships to two topic schemes.
"""

import logging

from api.models import Launch

from bot.app.notifications.base import NotificationResult
from bot.app.notifications.metrics import record_send, record_skip
from bot.utils.notification_groups import agency_group, location_group
from bot.utils.util import (
    V6_AUDIENCE_CLASSES,
    V6_NOTIFICATION_TYPES,
    build_v6_broadcast_condition,
    build_v6_condition,
    v6_class_is_webcast_only,
)

logger = logging.getLogger(__name__)

_PLATFORMS = ("android", "ios")


class V6NotificationMixin:
    """Per-audience-class dispatch. Requires V5NotificationMixin in the MRO for
    ``_build_v5_data_payload`` -- see the module docstring in v5.py."""

    def send_v6_launch_notification(
        self, launch: Launch, notification_type: str, contents: str
    ) -> list[NotificationResult]:
        """Send one message per satisfiable audience class, per platform."""
        # Deliberately rebuilds the payload V5 just built: threading the dict
        # through would mean modifying send_v5_notification, which the dual-send
        # window forbids. The extra queries are the price of V5 being untouched.
        data = self._build_v5_data_payload(launch, notification_type, contents)
        env = "debug" if self.DEBUG else "prod"
        has_webcast = data["webcast"] == "True"

        lsp_id = launch.launch_service_provider.id if launch.launch_service_provider else None
        location_id = launch.pad.location.id if launch.pad and launch.pad.location else None
        agency = agency_group(lsp_id)
        location = location_group(location_id)

        results: list[NotificationResult] = []
        for platform in _PLATFORMS:
            for audience_class in V6_AUDIENCE_CLASSES:
                if v6_class_is_webcast_only(audience_class) and not has_webcast:
                    continue
                condition = build_v6_condition(
                    env=env,
                    platform=platform,
                    audience_class=audience_class,
                    notification_type=notification_type,
                    agency_group=agency,
                    location_group=location,
                )
                if condition is None:
                    if notification_type not in V6_NOTIFICATION_TYPES:
                        reason = "unknown_type"
                    elif not agency:
                        reason = "unmapped_agency"
                    else:
                        reason = "unmapped_location"
                    logger.warning(
                        f"V6 skip - class={audience_class} platform={platform} reason={reason} "
                        f"type={notification_type} lsp_id={lsp_id} location_id={location_id} "
                        f"launch={launch.id}"
                    )
                    record_skip(platform=platform, audience_class=audience_class, reason=reason)
                    continue
                results.append(
                    self._send_v6(
                        platform=platform,
                        data=data,
                        condition=condition,
                        audience_class=audience_class,
                        title=data["title"],
                        body=data["body"],
                        collapse_id=data["launch_uuid"],
                        category="launch",
                        # No platform segment: FCM caps analytics_label at 50
                        # chars and a 36-char UUID leaves no room for it. The
                        # platform is already carried by the condition, the
                        # topic names, and the `platform` metric label.
                        analytics_label=f"v6_{audience_class}_{data['launch_uuid']}",
                    )
                )
        return results

    def send_v6_broadcast(
        self,
        kind: str,
        v5_data: dict,
        title: str,
        body: str,
        collapse_id: str,
        category: str,
        platforms: tuple[str, ...] = _PLATFORMS,
    ) -> list[NotificationResult]:
        """Send a broadcast type (events / news / announce) to both platforms.

        Broadcasts are not agency/location filtered -- one topic per platform,
        gated by the user's own per-type toggle via their subscription.

        ``platforms`` narrows the send. Events and news keep the default because
        both of their platform sends live in one method; custom admin
        notifications carry independent ``send_ios`` / ``send_android`` flags and
        must pass the single platform they are dispatching for.
        """
        env = "debug" if self.DEBUG else "prod"
        results: list[NotificationResult] = []
        for platform in platforms:
            results.append(
                self._send_v6(
                    platform=platform,
                    data=v5_data,
                    condition=build_v6_broadcast_condition(env, platform, kind),
                    audience_class="broadcast",
                    title=title,
                    body=body,
                    collapse_id=collapse_id,
                    category=category,
                    analytics_label=f"v6_{platform}_{kind}_{collapse_id}",
                )
            )
        return results

    def _send_v6(
        self,
        *,
        platform: str,
        data: dict,
        condition: str,
        audience_class: str,
        title: str,
        body: str,
        collapse_id: str,
        category: str,
        analytics_label: str,
    ) -> NotificationResult:
        """One FCM call. Android is data-only; iOS carries the alert."""
        logger.info(f"V6 {platform} [{audience_class}] condition: {condition}")
        kwargs = {
            "data_payload": data,
            "topic_condition": condition,
            "fcm_options": {"analytics_label": analytics_label},
            # 30s, not V5's 240s. "Identical to V5" covers the payload and the
            # APNs/Android config, not the transport timeout: V6 adds up to 12
            # sequential blocking calls per launch on the single-threaded
            # tracker loop, and oneMinute/tenMinutes are notifications where
            # lateness equals uselessness. V5 runs first and keeps its 240s.
            "timeout": 30,
        }
        if platform == "android":
            kwargs["notification_title"] = None
            kwargs["notification_body"] = None
            kwargs["android_config"] = {
                "priority": "high",
                "collapse_key": collapse_id,
                "ttl": "86400s",
            }
        else:
            kwargs["notification_title"] = title
            kwargs["notification_body"] = body
            kwargs["apns_config"] = {
                "headers": {"apns-priority": "10", "apns-collapse-id": collapse_id},
                "payload": {"aps": {"mutable-content": 1}},
            }

        notification_type = data.get("notification_type")

        try:
            result = self.fcm.notify(**kwargs)
            logger.info(f"V6 {platform} [{audience_class}] result: {result}")
            record_send(
                platform=platform,
                category=category,
                success=True,
                result=result,
                audience_class=audience_class,
            )
            return NotificationResult(
                notification_type=notification_type,
                topics=condition,
                result=result,
                analytics_label=analytics_label,
                error=None,
            )
        except Exception as e:
            logger.error(f"V6 {platform} [{audience_class}] error: {e}")
            record_send(platform=platform, category=category, success=False, audience_class=audience_class)
            return NotificationResult(
                notification_type=notification_type,
                topics=condition,
                result=None,
                analytics_label=analytics_label,
                error=e,
            )
