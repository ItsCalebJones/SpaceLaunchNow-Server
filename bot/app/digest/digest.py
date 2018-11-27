import logging

import bot.app.digest.daily as daily_check
import bot.app.digest.weekly as weekly_check
from bot.utils.config import keys

# import the logging library

# Get an instance of a logger
from spacelaunchnow import config

logger = logging.getLogger('digest')

AUTH_TOKEN_HERE = keys['AUTH_TOKEN_HERE']
APP_ID = keys['APP_ID']
DAEMON_SLEEP = 6000


class DigestServer:
    def __init__(self, debug=None, version=None):

        if debug is None:
            self.DEBUG = config.DEBUG
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

