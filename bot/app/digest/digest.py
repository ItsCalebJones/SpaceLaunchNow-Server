
import re
import logging
import pytz
from django.core import serializers
from num2words import num2words
from django.utils.datetime_safe import datetime, time
from twitter import Twitter, OAuth, TwitterHTTPError

import bot.app.digest.daily as daily_check
import bot.app.digest.weekly as weekly_check
from bot.libraries.launchlibrarysdk import LaunchLibrarySDK
from bot.models import Notification, DailyDigestRecord
from bot.utils.config import keys
from bot.utils.deserializer import launch_json_to_model
# import the logging library

# Get an instance of a logger
logger = logging.getLogger('bot.digest')

AUTH_TOKEN_HERE = keys['AUTH_TOKEN_HERE']
APP_ID = keys['APP_ID']
DAEMON_SLEEP = 6000


class DigestServer:
    def __init__(self, debug=None, version=None):

        if debug is None:
            self.DEBUG = False
        else:
            self.DEBUG = debug

        self.time_to_next_launch = None
        self.next_launch = None

    def run(self, daily=False, weekly=False):
        if daily:
            daily_check.check_launch_daily(self.DEBUG)
        elif weekly:
            weekly_check.check_launch_weekly(self.DEBUG)
        else:
            logger.error("Both daily and weekly false...ignoring request.")
