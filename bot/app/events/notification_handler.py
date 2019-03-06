import logging
from datetime import datetime

import pytz
from pyfcm import FCMNotification

from bot.utils.config import keys
from bot.utils.util import get_fcm_topics_v1, get_fcm_topics_v2
from spacelaunchnow import config

logger = logging.getLogger('events')


class EventNotificationHandler:
    def __init__(self, debug=None):
        if debug is None:
            self.DEBUG = config.DEBUG
        else:
            self.DEBUG = debug

    def send_ten_minute_notification(self, event):
        data = self.build_data(event)

    def send_webcast_notification(self, event):
        data = self.build_data(event)

    def build_data(self, event):
        return {
            "type": "event",
            "event_id": event.id,
            "event_name": event.name,
            "event_description": event.description,
            "event_type_id": event.type.id,
            "event_type_name": event.type.name,
            "event_date": event.date.strftime("%B %d, %Y %H:%M:%S %Z"),
            "event_location": event.location,
            "event_news_url": event.news_url,
        }

    def build_topics(self, event):
        if self.DEBUG:
            topic = "'debug_v2' in topics && 'events' in topics && '%s' in topics" % event.type.name
        else:
            topic = "'prod_v2' in topics && 'events' in topics && '%s' in topics" % event.type.name
        return topic

    def send_notification(self, topics, data):
        pass
