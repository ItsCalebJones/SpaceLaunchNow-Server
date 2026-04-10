import json
import logging

from bot.app.notification_service import NotificationService
from bot.utils.util import get_fcm_v5_android_topic, get_fcm_v5_ios_topic

logger = logging.getLogger(__name__)


class EventNotificationHandler(NotificationService):
    def send_ten_minute_notification(self, event):
        self.send_notification(event, "event_notification")

    def send_webcast_notification(self, event):
        self.send_notification(event, "event_webcast", webcast=True)

    def build_data(self, event, type):
        webcast = bool(event.vid_urls.first())

        feature_image = None
        if event.image.image and hasattr(event.image.image, "url"):
            feature_image = event.image.image.url

        data = {
            "notification_type": type,
            "click_action": "FLUTTER_NOTIFICATION_CLICK",
            "event": {
                "id": event.id,
                "name": event.name,
                "description": event.description,
                "type": {
                    "id": event.type.id,
                    "name": event.type.name,
                },
                "date": event.date.strftime("%B %d, %Y %H:%M:%S %Z"),
                "location": event.location,
                "news_url": getattr(event.info_urls.first(), "info_url", None),
                "video_url": getattr(event.vid_urls.first(), "vid_url", None),
                "webcast_live": event.webcast_live,
                "feature_image": feature_image,
            },
            "webcast": str(webcast),
        }

        data["event"] = json.dumps(data["event"])

        return data

    def _build_v5_event_data(self, event, event_type, webcast: bool = False):
        """Build V5-compatible flat data payload for event notifications.

        V5 payloads use flat key-value strings (FCM requirement) with an
        'event_id' field so the KMP app can detect this is an event notification
        and deep-link to the event detail screen.
        """
        feature_image = None
        if event.image.image and hasattr(event.image.image, "url"):
            feature_image = event.image.image.url

        description = event.description or ""
        message_body = "Live webcast is available!" if webcast else description

        data = {
            "notification_type": event_type,
            "title": event.name,
            "body": message_body,
            "event_id": str(event.id),
            "event_name": event.name,
            "event_description": description[:500] if description else "",
            "event_type_id": str(event.type.id) if event.type else "",
            "event_type_name": event.type.name if event.type else "",
            "event_date": event.date.strftime("%Y-%m-%dT%H:%M:%SZ") if event.date else "",
            "event_location": event.location or "",
            "event_news_url": getattr(event.info_urls.first(), "info_url", "") or "",
            "event_video_url": getattr(event.vid_urls.first(), "vid_url", "") or "",
            "event_webcast_live": str(event.webcast_live),
            "event_feature_image": feature_image or "",
            "webcast": str(webcast),
        }

        return data

    def build_v3_topics(self):
        if self.DEBUG:
            topic = "'debug_v3' in topics && 'events' in topics"
        else:
            topic = "'prod_v3' in topics && 'events' in topics"
        return topic

    def build_flutter_v3_topics(self):
        if self.DEBUG:
            topic = "'flutter_debug_v3' in topics && 'events' in topics"
        else:
            topic = "'flutter_production_v3' in topics && 'events' in topics"
        return topic

    def send_notification(self, event, event_type, webcast: bool = False):
        data = self.build_data(event, event_type)

        # Send V3 Android notif
        self.send_to_fcm(self.build_v3_topics(), data, webcast)

        # Send V3 Flutter notif
        self.send_flutter_to_fcm(self.build_flutter_v3_topics(), data, webcast)

        # Send V5 notifications (KMP app)
        self._send_v5_event_notification(event, event_type, webcast)

    def _send_v5_event_notification(self, event, event_type, webcast: bool = False):
        """Send event notifications to V5 Android and iOS topics."""
        v5_data = self._build_v5_event_data(event, event_type, webcast)

        # V5 Android (data-only)
        android_topics = get_fcm_v5_android_topic(debug=self.DEBUG)
        logger.info("----------------------------------------------------------")
        logger.info("V5 Android Event Notification")
        logger.info(f"Notification Data: {v5_data}")
        logger.info(f"Topics: {android_topics}")
        try:
            android_result = self.fcm.notify(
                data_payload=v5_data,
                topic_condition=android_topics,
                notification_title=None,
                notification_body=None,
                fcm_options={"analytics_label": f"v5_android_event_{v5_data['event_id']}"},
                android_config={
                    "priority": "high",
                    "collapse_key": f"event_{v5_data['event_id']}",
                    "ttl": "86400s",
                },
                timeout=240,
            )
            logger.info(f"V5 Android Event Result: {android_result}")
        except Exception as e:
            logger.error(f"V5 Android Event Notification Error: {e}")
        logger.info("----------------------------------------------------------")

        # V5 iOS (alert with mutable-content)
        ios_topics = get_fcm_v5_ios_topic(debug=self.DEBUG)
        logger.info("----------------------------------------------------------")
        logger.info("V5 iOS Event Notification")
        logger.info(f"Notification Data: {v5_data}")
        logger.info(f"Topics: {ios_topics}")
        try:
            ios_result = self.fcm.notify(
                data_payload=v5_data,
                topic_condition=ios_topics,
                notification_title=v5_data["title"],
                notification_body=v5_data["body"],
                fcm_options={"analytics_label": f"v5_ios_event_{v5_data['event_id']}"},
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
            logger.info(f"V5 iOS Event Result: {ios_result}")
        except Exception as e:
            logger.error(f"V5 iOS Event Notification Error: {e}")
        logger.info("----------------------------------------------------------")

    def send_to_fcm(self, topics, data, webcast: bool = False):
        logger.info("----------------------------------------------------------")
        logger.info(f"Notification Data: {data}")
        logger.info(f"Topics: {topics}")

        event_info = json.loads(data["event"])
        message_body = "Live webcast is available!" if webcast else event_info["description"]

        notification = self.fcm.notify(
            topic_condition=topics,
            notification_title=event_info["name"],
            notification_body=message_body,
        )

        logger.info(notification)
        logger.info("----------------------------------------------------------")

    def send_flutter_to_fcm(self, topics, data, webcast: bool = False):
        logger.info("----------------------------------------------------------")
        logger.info("Flutter Notification")
        logger.info(f"Notification Data: {data}")
        logger.info(f"Topics: {topics}")

        event_info = json.loads(data["event"])

        message_body = "Live webcast is available!" if webcast else event_info["description"]
        notification = self.fcm.notify(
            data_payload=data,
            topic_condition=topics,
            notification_title=event_info["name"],
            notification_body=message_body,
        )
        logger.info(notification)
        logger.info("----------------------------------------------------------")
