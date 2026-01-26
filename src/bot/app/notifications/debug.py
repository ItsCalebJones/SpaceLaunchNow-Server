"""Debug notification utilities."""

import logging
import uuid

from bot.app.notifications.base import NotificationResult

logger = logging.getLogger(__name__)


class DebugNotificationMixin:
    """Mixin for debug notification methods."""

    def send_debug_notif(self):
        """Send a debug notification for testing."""
        if self.DEBUG:
            topics = "'debug_v3' in topics && 'newZealand' in topics"  # noqa: E501
            generated = str(uuid.uuid4())
            analytics_label = f"debug_test_topics_{generated}"

            results = self.fcm.notify(
                topic_condition=topics,
                notification_title="Test Notification",
                notification_body=f"{generated}\n{topics}",
                android_config={"priority": "high", "collapse_key": generated, "ttl": "86400s"},
                fcm_options={"analytics_label": analytics_label},
            )

            logger.info(f"NOTIF: {results} - {generated}")
            self.notify_discord(
                [
                    NotificationResult(
                        notification_type="Debug",
                        topics=topics,
                        analytics_label=analytics_label,
                        result=results,
                        error=None,
                    )
                ],
                data=None,
            )
