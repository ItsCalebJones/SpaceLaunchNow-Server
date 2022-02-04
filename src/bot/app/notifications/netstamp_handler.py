import logging
from datetime import datetime, timedelta

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
        self.social_handler = SocialEvents()
        self.notification_handler = NotificationHandler()

    def netstamp_changed(self, launch, notification, diff):
        logger.info('Netstamp change detected for %s - now launching in %d seconds.' % (launch.name, diff))
        now = datetime.now(tz=pytz.utc)
        old = notification.last_net_stamp
        new = launch.net
        self.update_notification_record(diff, launch, notification)

        if new <= now + timedelta(hours=72) and old <= now + timedelta(hours=24):
            logger.info('Netstamp Changed and within window - sending mobile notification.')
            self.notification_handler.send_notification(launch, 'netstampChanged', notification)
        self.social_handler.send_to_twitter(launch, 'netstampChanged')

    def update_notification_record(self, diff, launch, notification):
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
        notification.last_twitter_post = datetime.now(tz=pytz.utc)
        notification.last_net_stamp = launch.net
        notification.last_net_stamp_timestamp = datetime.now(tz=pytz.utc)
        logger.info('Updating Notification %s to timestamp %s' % (launch.id,
                                                                  notification.last_twitter_post
                                                                  .strftime("%A %d. %B %Y")))
        notification.save()
