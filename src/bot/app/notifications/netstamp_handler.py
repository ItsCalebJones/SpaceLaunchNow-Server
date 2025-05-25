import logging
from datetime import datetime, timedelta

import pytz

from bot.app.notifications.notification_handler import NotificationHandler
from spacelaunchnow import settings

logger = logging.getLogger(__name__)


class NetstampHandler:
    def __init__(self, debug=settings.DEBUG):
        self.DEBUG = debug
        self.notification_handler = NotificationHandler()

    def netstamp_changed(self, launch, notification, diff):
        logger.info(f"Netstamp change detected for {launch.name} - now launching in {diff} seconds.")
        now = datetime.now(tz=pytz.utc)
        old = notification.last_net_stamp
        new = launch.net
        self.update_notification_record(diff, launch, notification)

        if new <= now + timedelta(hours=72) and old <= now + timedelta(hours=24):
            logger.info("Netstamp Changed and within window - sending mobile notification.")
            self.notification_handler.send_notification(launch, "netstampChanged", notification)

    def update_notification_record(self, diff, launch, notification):
        # If launch is within 24 hours...
        if 86400 >= diff > 3600:
            logger.info("Launch is within 24 hours, resetting notifications.")
            notification.wasNotifiedTwentyFourHour = True
            notification.wasNotifiedOneHour = False
            notification.wasNotifiedTenMinutes = False

        elif 3600 >= diff > 600:
            logger.info("Launch is within one hour, resetting Ten minute notifications.")
            notification.wasNotifiedOneHour = True
            notification.wasNotifiedTwentyFourHour = True

        elif diff <= 600:
            logger.info("Launch is within ten minutes.")
            notification.wasNotifiedOneHour = True
            notification.wasNotifiedTwentyFourHour = True
            notification.wasNotifiedTenMinutes = True

        elif diff >= 86400:
            notification.wasNotifiedTwentyFourHour = False
            notification.wasNotifiedOneHour = False
            notification.wasNotifiedTenMinutes = False

        notification.last_net_stamp = launch.net
        notification.last_net_stamp_timestamp = datetime.now(tz=pytz.utc)
        timestamp = notification.last_net_stamp_timestamp.strftime("%A %d. %B %Y")
        logger.info(f"Updating Notification {launch.id} to timestamp {timestamp}")
        notification.save()
