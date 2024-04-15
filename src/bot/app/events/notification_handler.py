import logging

from pyfcm import FCMNotification

from spacelaunchnow import settings

logger = logging.getLogger(__name__)


class EventNotificationHandler:
    def __init__(self, debug=settings.DEBUG):
        self.DEBUG = debug
        self.api_key = settings.FCM_KEY

    def send_ten_minute_notification(self, event):
        self.send_notification(event, "event_notification")

    def send_webcast_notification(self, event):
        self.send_notification(event, "event_webcast", webcast=True)

    def build_data(self, event, type):
        webcast = bool(event.video_url)

        feature_image = None
        if event.feature_image and hasattr(event.feature_image, "url"):
            feature_image = event.feature_image.url

        return {
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
            "webcast": webcast,
        }

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
        self.send_to_fcm(self.build_v3_topics(), data)

        # Send Flutter notif
        self.send_flutter_to_fcm(self.build_flutter_v3_topics(), data, webcast)

    def send_to_fcm(self, topics, data):
        logger.info("----------------------------------------------------------")
        logger.info("Notification Data: %s" % data)
        logger.info("Topics: %s" % topics)
        push_service = FCMNotification(api_key=self.api_key)
        notification = push_service.notify_topic_subscribers(data_message=data, condition=topics, time_to_live=86400)
        logger.info(notification)
        logger.info("----------------------------------------------------------")

    def send_flutter_to_fcm(self, topics, data, webcast: bool = False):
        logger.info("----------------------------------------------------------")
        logger.info("Flutter Notification")
        logger.info("Notification Data: %s" % data)
        logger.info("Topics: %s" % topics)
        push_service = FCMNotification(api_key=self.api_key)
        message_body = "Live webcast is available!" if webcast else data["event"]["description"]
        notification = push_service.notify_topic_subscribers(
            data_message=data,
            condition=topics,
            time_to_live=86400,
            message_title=data["event"]["name"],
            message_body=message_body,
        )
        logger.info(notification)
        logger.info("----------------------------------------------------------")
