import json
import logging

from bot.app.notification_service import NotificationService

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
                "news_url": event.info_urls.first(),
                "video_url": event.vid_urls.first(),
                "webcast_live": event.webcast_live,
                "feature_image": feature_image,
            },
            "webcast": str(webcast),
        }

        data["event"] = json.dumps(data["event"])

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

        # Send Android notif
        self.send_to_fcm(self.build_v3_topics(), data, webcast)

        # Send Flutter notif
        self.send_flutter_to_fcm(self.build_flutter_v3_topics(), data, webcast)

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
