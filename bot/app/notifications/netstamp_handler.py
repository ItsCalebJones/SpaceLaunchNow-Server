import logging
from datetime import datetime

import pytz

from bot.app.notifications.notification_handler import NotificationHandler
from bot.app.notifications.social_handler import SocialEvents
from bot.utils.util import seconds_to_time
from spacelaunchnow import config

logger = logging.getLogger('bot.notifications')


class NetstampHandler:
    def __init__(self, debug=None):
        if debug is None:
            self.DEBUG = config.DEBUG
        else:
            self.DEBUG = debug
        self.twitter_handler = SocialEvents()
        self.notification_handler = NotificationHandler()

    def netstamp_changed(self, launch, notification, diff):
        logger.info('Netstamp change detected for %s - now launching in %d seconds.' % (launch.name, diff))
        date = launch.net
        message = 'SCHEDULE UPDATE: %s now launching in %s at %s.' % (launch.name,
                                                                      seconds_to_time(diff),
                                                                      date.strftime("%H:%M %Z (%d/%m)"))

        old_diff = notification.last_net_stamp - datetime.now(tz=pytz.utc)
        if old_diff.total_seconds() < 604800:
            logger.info('Netstamp Changed and within window - sending mobile notification.')
            self.notification_handler.send_notification(launch, 'netstampChanged', notification)
        self.twitter_handler.send_to_twitter(launch, notification, 'netstampChanged')

        notification.last_net_stamp = notification.launch.net
        notification.last_net_stamp_timestamp = datetime.now(tz=pytz.utc)
        launch.save()

        # If launch is within 24 hours...
        if 86400 >= diff > 3600:
            logger.info('Launch is within 24 hours, resetting notifications.')
            notification.wasNotifiedTwentyFourHour = True
            notification.wasNotifiedOneHour = False
            notification.wasNotifiedTenMinutes = False

            notification.wasNotifiedTwentyFourHourTwitter = True
            notification.wasNotifiedOneHourTwitter = False
            notification.wasNotifiedTenMinutesTwitter = False

            notification.wasNotifiedTwentyFourHourDiscord = True
            notification.wasNotifiedOneHourDiscord = False
            notification.wasNotifiedTenMinutesDiscord = False
        elif 3600 >= diff > 600:
            logger.info('Launch is within one hour, resetting Ten minute notifications.')
            notification.wasNotifiedOneHour = True
            notification.wasNotifiedTwentyFourHour = True

            notification.wasNotifiedOneHourTwitter = True
            notification.wasNotifiedTwentyFourHourTwitter = True

            notification.wasNotifiedOneHourDiscord = True
            notification.wasNotifiedTwentyFourHourDiscord = True
        elif diff <= 600:
            logger.info('Launch is within ten minutes.')
            notification.wasNotifiedOneHour = True
            notification.wasNotifiedTwentyFourHour = True
            notification.wasNotifiedTenMinutes = True

            notification.wasNotifiedOneHourTwitter = True
            notification.wasNotifiedTwentyFourHourTwitter = True
            notification.wasNotifiedTenMinutesTwitter = True

            notification.wasNotifiedOneHourDiscord = True
            notification.wasNotifiedTwentyFourHourDiscord = True
            notification.wasNotifiedTenMinutesDiscord = True
        elif diff >= 86400:
            notification.wasNotifiedTwentyFourHour = False
            notification.wasNotifiedOneHour = False
            notification.wasNotifiedTenMinutes = False

            notification.wasNotifiedTwentyFourHourTwitter = False
            notification.wasNotifiedOneHourTwitter = False
            notification.wasNotifiedTenMinutesTwitter = False

            notification.wasNotifiedTwentyFourHourDiscord = False
            notification.wasNotifiedOneHourDiscord = False
            notification.wasNotifiedTenMinutesDiscord = False
        notification.save()
