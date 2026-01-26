"""V4 notification handler for FCM with client-side filtering."""

import logging

from bot.app.notifications.base import NotificationResult

logger = logging.getLogger(__name__)


class V4NotificationMixin:
    """Mixin for V4 notification methods."""

    def send_notif_v4(
        self, data, topics, message_title=None, message_body=None, analytics_label: str = None
    ) -> NotificationResult:
        """Send a V4 notification via FCM with APNS support."""
        try:
            logger.info(f"Notification v4 Data - {data}")
            logger.info(f"Topic Data v4 - {topics}")

            results = self.fcm.notify(
                data_payload=data,
                topic_condition=topics,
                notification_title=message_title,
                notification_body=message_body,
                fcm_options={"analytics_label": analytics_label},
                android_config={"priority": "high", "collapse_key": data["launch_uuid"], "ttl": "86400s"},
                apns_config={
                    "headers": {
                        "apns-priority": "5",
                        "apns-push-type": "background",
                        "apns-topic": "me.spacelaunchnow.spacelaunchnow",
                    },
                    "payload": {
                        "aps": {
                            "content-available": 1,
                        }
                    },
                },
            )
            logger.info(results)
            return NotificationResult(
                notification_type=data["notification_type"],
                topics=topics,
                result=results,
                analytics_label=analytics_label,
                error=None,
            )
        except Exception as e:
            logger.error(e)
            return NotificationResult(
                notification_type=data["notification_type"],
                topics=topics,
                result=None,
                analytics_label=analytics_label,
                error=e,
            )
