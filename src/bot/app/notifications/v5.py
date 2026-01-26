"""V5 notification handler with platform-specific messaging.

This module provides a V5 notification system with distinct Android (data-only)
and iOS (mutable-content alert) message paths using prod_v5/debug_v5 topic
naming conventions.

Android notifications are data-only, allowing the app to construct the
notification display. iOS notifications include an alert with mutable-content
for Notification Service Extension processing, plus full data payload for
client-side filtering.
"""

import logging

from api.models import Launch

from bot.app.notifications.base import NotificationResult
from bot.utils.util import get_fcm_v5_android_topic, get_fcm_v5_ios_topic

logger = logging.getLogger(__name__)


class V5NotificationMixin:
    """Mixin for V5 notification methods with platform-specific paths.

    Sends notifications to Android and iOS devices using separate FCM
    configurations optimized for each platform:

    - Android: Data-only messages with high priority, app handles display
    - iOS: Alert messages with mutable-content for NSE processing
    """

    def send_notif_v5_ios(
        self, data: dict, topics: str, message_title: str = None, message_body: str = None, analytics_label: str = None
    ) -> NotificationResult:
        """Send alert notification to iOS devices with mutable-content.

        iOS notifications include a visible alert with mutable-content: 1
        to enable Notification Service Extension processing. The full data
        payload is included for client-side filtering.

        Args:
            data: The data payload dictionary
            topics: FCM topic condition string
            message_title: Notification title
            message_body: Notification body
            analytics_label: Label for FCM analytics

        Returns:
            NotificationResult with the FCM response
        """
        try:
            logger.info(f"V5 iOS Notification Data - {data}")
            logger.info(f"V5 iOS Topics - {topics}")

            results = self.fcm.notify(
                data_payload=data,
                topic_condition=topics,
                notification_title=message_title,
                notification_body=message_body,
                fcm_options={"analytics_label": analytics_label},
                apns_config={
                    "headers": {
                        "apns-priority": "10",
                    },
                    "payload": {
                        "aps": {
                            "mutable-content": 1,
                        },
                    },
                },
                timeout=240,
            )
            logger.info(f"V5 iOS Result: {results}")
            return NotificationResult(
                notification_type=data["notification_type"],
                topics=topics,
                result=results,
                analytics_label=analytics_label,
                error=None,
            )
        except Exception as e:
            logger.error(f"V5 iOS Notification Error: {e}")
            return NotificationResult(
                notification_type=data["notification_type"],
                topics=topics,
                result=None,
                analytics_label=analytics_label,
                error=e,
            )

    def send_notif_v5_android(
        self, data: dict, topics: str, message_title: str = None, message_body: str = None, analytics_label: str = None
    ) -> NotificationResult:
        """Send data-only notification to Android devices.

        Android notifications are data-only, allowing the app to construct
        the notification display with full control over appearance.

        Args:
            data: The data payload dictionary (should include title/body for app to display)
            topics: FCM topic condition string
            message_title: Not used for Android (passed via data payload)
            message_body: Not used for Android (passed via data payload)
            analytics_label: Label for FCM analytics

        Returns:
            NotificationResult with the FCM response
        """
        try:
            logger.info(f"V5 Android Notification Data - {data}")
            logger.info(f"V5 Android Topics - {topics}")

            results = self.fcm.notify(
                data_payload=data,
                topic_condition=topics,
                notification_title=None,
                notification_body=None,
                fcm_options={"analytics_label": analytics_label},
                android_config={
                    "priority": "high",
                    "collapse_key": data["launch_uuid"],
                    "ttl": "86400s",
                },
                timeout=240,
            )
            logger.info(f"V5 Android Result: {results}")
            return NotificationResult(
                notification_type=data["notification_type"],
                topics=topics,
                result=results,
                analytics_label=analytics_label,
                error=None,
            )
        except Exception as e:
            logger.error(f"V5 Android Notification Error: {e}")
            return NotificationResult(
                notification_type=data["notification_type"],
                topics=topics,
                result=None,
                analytics_label=analytics_label,
                error=e,
            )

    def send_v5_notification(
        self,
        launch: Launch,
        notification_type: str,
        contents: str,
    ) -> list[NotificationResult]:
        """Send v5 notifications to both Android and iOS platforms.

        Args:
            launch: The Launch object to send notification for
            notification_type: Type of notification (e.g., 'tenMinutes', 'oneHour')
            contents: The notification message body

        Returns:
            List of NotificationResult objects for Android and iOS
        """
        data = self._build_v5_data_payload(launch, notification_type, contents)

        # Android notification (data-only)
        android_topics = get_fcm_v5_android_topic(debug=self.DEBUG)
        android_result = self.send_notif_v5_android(
            data=data,
            topics=android_topics,
            analytics_label=f"v5_android_{data['launch_uuid']}",
        )

        # iOS notification (alert with mutable-content)
        ios_topics = get_fcm_v5_ios_topic(debug=self.DEBUG)
        ios_result = self.send_notif_v5_ios(
            data=data,
            topics=ios_topics,
            message_title=launch.name,
            message_body=contents,
            analytics_label=f"v5_ios_{data['launch_uuid']}",
        )

        return [android_result, ios_result]

    def _build_v5_data_payload(self, launch: Launch, notification_type: str, contents: str) -> dict:
        """Build the v5 data payload with display and filtering fields.

        Args:
            launch: The Launch object
            notification_type: Type of notification
            contents: The notification message body

        Returns:
            Dictionary containing all notification data fields
        """
        webcast = len(launch.vid_urls.all()) > 0

        # Get image URL
        image = ""
        if launch.image:
            image = launch.image.image.url
        elif launch.rocket and launch.rocket.configuration and launch.rocket.configuration.image:
            image = launch.rocket.configuration.image.image.url
        elif launch.launch_service_provider and launch.launch_service_provider.image:
            image = launch.launch_service_provider.image.image.url

        # Build program IDs as comma-separated string
        program_ids = ",".join(str(p.id) for p in launch.program.all()) if launch.program.exists() else ""

        data = {
            # Display fields (title/body for Android to construct notification)
            "notification_type": notification_type,
            "title": launch.name,
            "body": contents,
            "launch_uuid": str(launch.id),
            "launch_id": str(launch.id),
            "launch_name": launch.name,
            "launch_image": image,
            "launch_net": launch.net.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "launch_location": launch.pad.location.name,
            "webcast": str(webcast),
            "webcast_live": str(launch.webcast_live),
            # Client-side filtering IDs (as strings for FCM compatibility)
            "lsp_id": str(launch.launch_service_provider.id) if launch.launch_service_provider else "",
            "location_id": str(launch.pad.location.id) if launch.pad and launch.pad.location else "",
            "program_id": program_ids,
            "status_id": str(launch.status.id) if launch.status else "",
            "orbit_id": str(launch.mission.orbit.id) if launch.mission and launch.mission.orbit else "",
            "mission_type_id": str(launch.mission.mission_type.id)
            if launch.mission and launch.mission.mission_type
            else "",
            "launcher_family_id": (
                str(launch.rocket.configuration.families.first().id)
                if launch.rocket and launch.rocket.configuration and launch.rocket.configuration.families.exists()
                else ""
            ),
        }

        return data
