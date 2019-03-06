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
        pass

    def send_webcast_notification(self, event):
        pass