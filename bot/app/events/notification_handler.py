import logging
from datetime import datetime

import pytz
from pyfcm import FCMNotification

from api.endpoints.sln.v330.events.serializers import EventsSerializer
from spacelaunchnow.config import keys
from bot.utils.util import get_fcm_topics_v1, get_fcm_topics_v2
from spacelaunchnow import config

logger = logging.getLogger('bot.events')


class EventNotificationHandler:
    def __init__(self, debug=None):
        if debug is None:
            self.DEBUG = config.DEBUG
        else:
            self.DEBUG = debug

    def send_ten_minute_notification(self, event):
        self.send_notification(self.build_topics(event),
                               self.build_data(event, 'event_notification'))
        self.send_flutter_notification(self.build_flutter_topics(event),
                                       self.build_data(event, 'event_notification'))

    def send_webcast_notification(self, event):
        self.send_notification(self.build_topics(event),
                               self.build_data(event, 'event_webcast'))
        self.send_flutter_notification(self.build_flutter_topics(event),
                                       self.build_data(event, 'event_webcast'),
                                       webcast=True)

    def build_data(self, event, type):
        if event.video_url:
            webcast = True
        else:
            webcast = False

        feature_image = None
        if event.feature_image and hasattr(event.feature_image, 'url'):
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
                "news_url": event.news_url,
                "video_url": event.video_url,
                "webcast_live": event.webcast_live,
                "feature_image": feature_image,
            },
            "webcast": webcast
        }

    def build_topics(self, event):
        if self.DEBUG:
            topic = "'debug_v2' in topics && 'events' in topics"
        else:
            topic = "'prod_v2' in topics && 'events' in topics"
        return topic

    def send_notification(self, topics, data):
        logger.info('----------------------------------------------------------')
        logger.info('Notification Data: %s' % data)
        logger.info('Topics: %s' % topics)
        push_service = FCMNotification(api_key=keys['FCM_KEY'])
        notification = push_service.notify_topic_subscribers(data_message=data,
                                                             condition=topics,
                                                             time_to_live=86400)
        logger.info(notification)
        logger.info('----------------------------------------------------------')

    def build_flutter_topics(self, event):
        if self.DEBUG:
            topic = "'flutter_debug_v2' in topics && 'events' in topics"
        else:
            topic = "'flutter_production_v2' in topics && 'events' in topics"
        return topic

    def send_flutter_notification(self, topics, data, webcast: bool = False):
        logger.info('----------------------------------------------------------')
        logger.info('Flutter Notification')
        logger.info('Notification Data: %s' % data)
        logger.info('Topics: %s' % topics)
        push_service = FCMNotification(api_key=keys['FCM_KEY'])
        if webcast:
            message_body = "Live webcast is available!"
        else:
            message_body = data['event']['description']
        notification = push_service.notify_topic_subscribers(data_message=data,
                                                             condition=topics,
                                                             time_to_live=86400,
                                                             message_title=data['event']['name'],
                                                             message_body=message_body)
        logger.info(notification)
        logger.info('----------------------------------------------------------')


