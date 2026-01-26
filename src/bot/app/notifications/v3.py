"""V3 and V3.5 notification handlers for FCM."""

import logging

from bot.app.notifications.base import NotificationResult

logger = logging.getLogger(__name__)


class V3NotificationMixin:
    """Mixin for V3 notification methods."""

    def send_notif_v3(
        self, data, topics, message_title=None, message_body=None, analytics_label: str = None
    ) -> NotificationResult:
        """Send a V3 notification via FCM."""
        try:
            logger.info(f"Notification v3 Data - {data}")
            logger.info(f"Topic Data v3- {topics}")
            results = self.fcm.notify(
                data_payload=data,
                topic_condition=topics,
                notification_title=message_title,
                notification_body=message_body,
                fcm_options={"analytics_label": analytics_label},
                android_config={"priority": "high", "collapse_key": data["launch_uuid"], "ttl": "86400s"},
                timeout=240,
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

    def send_notif_v3_5(
        self, data, topics, message_title=None, message_body=None, analytics_label: str = None
    ) -> NotificationResult:
        """Send a V3.5 notification via FCM with image support."""
        try:
            logger.info(f"Notification v3.5 Custom Data - {data}")
            logger.info(f"Topic Data v3.5- {topics}")
            results = self.fcm.notify(
                notification_title=message_title,
                notification_body=f"{message_body} {topics if self.DEBUG else ''}",
                notification_image=data["launch_image"],
                data_payload=data,
                topic_condition=topics,
                # Remove notification_title and notification_body to ensure custom handling
                fcm_options={"analytics_label": analytics_label},
                android_config={"priority": "high", "collapse_key": data["launch_uuid"], "ttl": "86400s"},
                timeout=240,
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
