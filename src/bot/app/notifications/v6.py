"""V6 topic-targeted notification dispatch.

Where V5 broadcasts one message per platform and lets the device filter, V6
sends one message per *audience class* with an FCM condition naming the
launch's own attributes. A device subscribes to the type topics of exactly one
class, so at most one condition can match it -- duplicate delivery is
impossible by construction rather than by deduplication.

Payloads and APNs/Android config are identical to V5 on purpose: during the
dual-send window one payload shape ships to two topic schemes.

Broadcasts (events / news / announce) are plain module functions rather than
mixin methods. They need nothing from ``self`` but the FCM client and the debug
flag, and keeping them free of the class hierarchy means the four handlers that
send them share one implementation instead of four copies.
"""

import logging
from concurrent.futures import ThreadPoolExecutor

from bot.app.notifications.base import NotificationResult
from bot.app.notifications.metrics import record_group_fallback, record_skip, record_v6_send
from bot.utils.notification_groups import (
    DEFAULT_AGENCY_GROUP,
    DEFAULT_LOCATION_GROUP,
    agency_group,
    location_group,
)
from bot.utils.util import (
    STARLINK_PROGRAM_ID,
    V6_AUDIENCE_CLASSES,
    build_v6_broadcast_condition,
    build_v6_condition,
    v6_class_is_webcast_only,
)

logger = logging.getLogger(__name__)

PLATFORMS = ("android", "ios")

# 30s, not V5's 240s. "Identical to V5" covers the payload and the APNs/Android
# config, not the transport timeout: V6 adds up to 12 blocking calls per launch
# on the tracker loop (fanned out MAX_CONCURRENT_SENDS at a time), and
# oneMinute/tenMinutes are notifications where lateness equals uselessness.
# V5 runs first and keeps 240s.
SEND_TIMEOUT_SECONDS = 30

# Bounded fan-out for the per-class launch sends. pyfcm is built for this --
# each pool thread lazily gets its own requests session via threading.local --
# and 6 workers caps a full 12-send webcast launch at ~2 network round-trip
# rounds instead of 12, while keeping the worst case (every send stalling to
# its 30s timeout) at ~60s rather than 6 minutes on the tracker loop.
MAX_CONCURRENT_SENDS = 6


def send_v6(
    fcm,
    *,
    platform: str,
    data: dict,
    condition: str,
    audience_class: str,
    category: str,
    collapse_id: str,
    analytics_label: str,
) -> NotificationResult:
    """One FCM call. Android is data-only; iOS carries the alert.

    Title and body are read from ``data``, which every V5 payload builder
    populates -- passing them separately only creates a way for them to disagree.
    """
    logger.info(f"V6 {platform} [{audience_class}] condition: {condition}")
    kwargs = {
        "data_payload": data,
        "topic_condition": condition,
        "fcm_options": {"analytics_label": analytics_label},
        "timeout": SEND_TIMEOUT_SECONDS,
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
        kwargs["notification_title"] = data["title"]
        kwargs["notification_body"] = data["body"]
        kwargs["apns_config"] = {
            "headers": {"apns-priority": "10", "apns-collapse-id": collapse_id},
            "payload": {"aps": {"mutable-content": 1}},
        }

    notification_type = data.get("notification_type")

    try:
        result = fcm.notify(**kwargs)
        logger.info(f"V6 {platform} [{audience_class}] result: {result}")
        record_v6_send(platform=platform, category=category, success=True, audience_class=audience_class)
        return NotificationResult(
            notification_type=notification_type,
            topics=condition,
            result=result,
            analytics_label=analytics_label,
            error=None,
        )
    except Exception as e:
        logger.error(f"V6 {platform} [{audience_class}] error: {e}")
        record_v6_send(platform=platform, category=category, success=False, audience_class=audience_class)
        return NotificationResult(
            notification_type=notification_type,
            topics=condition,
            result=None,
            analytics_label=analytics_label,
            error=e,
        )


def send_v6_broadcast(
    fcm,
    *,
    debug: bool,
    kind: str,
    data: dict,
    collapse_id: str,
    category: str,
    platforms: tuple[str, ...] = PLATFORMS,
) -> list[NotificationResult]:
    """Send a broadcast type (events / news / announce) to ``platforms``.

    Broadcasts are not agency/location filtered -- one topic per platform,
    gated by the user's own per-type toggle via their subscription.

    ``platforms`` narrows the send. Events and news keep the default because
    both of their platform sends live in one method; custom admin notifications
    carry independent ``send_ios`` / ``send_android`` flags and must pass the
    single platform they are dispatching for.
    """
    env = "debug" if debug else "prod"
    return [
        send_v6(
            fcm,
            platform=platform,
            data=data,
            condition=build_v6_broadcast_condition(env, platform, kind),
            audience_class="broadcast",
            category=category,
            collapse_id=collapse_id,
            analytics_label=f"v6_{platform}_{kind}_{collapse_id}",
        )
        for platform in platforms
    ]


def dual_send_v6_broadcast(
    fcm,
    *,
    debug: bool,
    kind: str,
    data: dict,
    collapse_id: str,
    category: str,
    platforms: tuple[str, ...] = PLATFORMS,
) -> None:
    """Send the V6 broadcast alongside a V5 one, containing any failure.

    Every V5 broadcast path calls this immediately after its own send. The
    containment is here rather than at each call site so there is one place to
    change it, and so no caller can forget it and let a V6 error abort a V5 flow.
    """
    try:
        send_v6_broadcast(
            fcm,
            debug=debug,
            kind=kind,
            data=data,
            collapse_id=collapse_id,
            category=category,
            platforms=platforms,
        )
    except Exception:
        logger.exception(f"V6 {kind} broadcast failed; the V5 send is unaffected")


class V6NotificationMixin:
    """Per-audience-class launch dispatch."""

    def send_v6_launch_notification(self, launch, notification_type: str, data: dict) -> list[NotificationResult]:
        """Send one message per satisfiable audience class, per platform.

        ``data`` is the V5 payload the caller already built; V6 ships the same
        payload shape, so rebuilding it here would double the ORM work on the
        latency-critical tracker loop for an identical dict.
        """
        env = "debug" if self.DEBUG else "prod"
        has_webcast = data["webcast"] == "True"

        lsp_id = launch.launch_service_provider.id if launch.launch_service_provider else None
        location_id = launch.pad.location.id if launch.pad and launch.pad.location else None
        agency = agency_group(lsp_id)
        location = location_group(location_id)

        # Read the program from the payload the V5 builder already traversed the
        # ORM for -- no extra query on the latency-critical tracker loop.
        mute_starlink = STARLINK_PROGRAM_ID in data.get("program_id", "").split(",")
        if mute_starlink:
            logger.info(f"V6 launch {launch.id} is Starlink; conditions exclude starlinkMuted subscribers")

        # A curated table missing an ID is invisible in delivery -- the send
        # still happens, just to a group almost nobody subscribes to. Count it.
        if agency == DEFAULT_AGENCY_GROUP:
            record_group_fallback("agency")
        if location == DEFAULT_LOCATION_GROUP:
            record_group_fallback("location")

        sends: list[dict] = []
        for platform in PLATFORMS:
            for audience_class in V6_AUDIENCE_CLASSES:
                if v6_class_is_webcast_only(audience_class) and not has_webcast:
                    # The expected, high-volume skip: this is why V6 sends per
                    # launch swing between 6 and 12. Recorded so that swing is
                    # explainable from metrics alone.
                    record_skip(platform=platform, audience_class=audience_class, reason="no_webcast")
                    continue
                condition, reason = build_v6_condition(
                    env=env,
                    platform=platform,
                    audience_class=audience_class,
                    notification_type=notification_type,
                    agency=agency,
                    location=location,
                    mute_starlink=mute_starlink,
                )
                if condition is None:
                    logger.warning(
                        f"V6 skip - class={audience_class} platform={platform} reason={reason} "
                        f"type={notification_type} lsp_id={lsp_id} location_id={location_id} "
                        f"launch={launch.id}"
                    )
                    record_skip(platform=platform, audience_class=audience_class, reason=reason)
                    continue
                sends.append(
                    dict(
                        platform=platform,
                        data=data,
                        condition=condition,
                        audience_class=audience_class,
                        category="launch",
                        collapse_id=data["launch_uuid"],
                        # No platform segment: FCM caps analytics_label at 50
                        # chars and a 36-char UUID leaves no room for it. The
                        # platform is already carried by the condition, the
                        # topic names, and the `platform` metric label.
                        analytics_label=f"v6_{audience_class}_{data['launch_uuid']}",
                    )
                )
        if not sends:
            return []
        # Fan out concurrently: send_v6 never raises (every FCM outcome is
        # caught into a NotificationResult and a counter), so pool.map cannot
        # blow up mid-flight, and result order matches spec order. Sequential
        # dispatch here made one stalled send delay every later class and the
        # next launch behind it.
        with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_SENDS) as pool:
            return list(pool.map(lambda kwargs: send_v6(self.fcm, **kwargs), sends))
