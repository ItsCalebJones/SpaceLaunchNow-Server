import logging

import bot.app.digest.daily as daily_check
import bot.app.digest.weekly as weekly_check
from spacelaunchnow import settings

logger = logging.getLogger(__name__)


class DigestServer:
    def __init__(self, debug=settings.DEBUG):
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

