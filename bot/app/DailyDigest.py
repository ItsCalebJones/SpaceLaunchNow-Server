from datetime import timedelta

import re
from django.utils.datetime_safe import datetime, time
from twitter import *
from bot.libraries.launchlibrarysdk import LaunchLibrarySDK
from bot.libraries.onesignalsdk import OneSignalSdk
from bot.models import Notification
from bot.utils.config import keys
from bot.utils.deserializer import json_to_model

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger('bot')

AUTH_TOKEN_HERE = keys['AUTH_TOKEN_HERE']
APP_ID = keys['APP_ID']
DAEMON_SLEEP = 6000


def update_notification_record(launch):
    notification = Notification.objects.get(launch=launch)
    notification.last_daily_digest_post = datetime.now()
    notification.last_net_stamp = launch.netstamp
    notification.last_net_stamp_timestamp = datetime.now()
    logger.info('Updating Notification %s to timestamp %s' % (notification.launch.id,
                                                           notification.last_daily_digest_post
                                                           .strftime("%A %d. %B %Y")))
    notification.save()


def daily_allowed():
    start_date = datetime.today() - timedelta(1)
    end_date = datetime.today()
    notifications = Notification.objects.filter(last_daily_digest_post__range=(start_date, end_date))
    for notification in notifications:
        if (notification.last_daily_digest_post - datetime.now()).total_seconds() < 86000:
            return False
    return True


class DailyDigestServer:
    def __init__(self):
        self.one_signal = OneSignalSdk(AUTH_TOKEN_HERE, APP_ID)
        self.launchLibrary = LaunchLibrarySDK(version='dev')
        response = self.one_signal.get_app(APP_ID)
        assert response.status_code == 200
        self.app = response.json()
        assert isinstance(self.app, dict)
        assert self.app['id'] and self.app['name'] and self.app['updated_at'] and self.app['created_at']
        self.app_auth_key = self.app['basic_auth_key']
        self.twitter = Twitter(
            auth=OAuth(keys['TOKEN_KEY'], keys['TOKEN_SECRET'], keys['CONSUMER_KEY'], keys['CONSUMER_SECRET'])
        )
        self.time_to_next_launch = None
        self.next_launch = None

    def run(self, daily=False, weekly=False):
        """The daemon's main loop for doing work
        :param weekly:
        :param daily:
        """
        if daily_allowed():
            if daily:
                self.check_launch_daily()
            if weekly:
                self.check_launch_weekly()
        else:
            logger.info("Daily already ran, skipping.")

    def check_launch_daily(self):
        response = self.launchLibrary.get_next_launches()
        if response.status_code is 200:
            response_json = response.json()
            launch_data = response_json['launches']
            logger.info("Found %i launches." % len(launch_data))
            launches = []
            for launch in launch_data:
                launch = json_to_model(launch)
                launches.append(launch)
            todays_launches = []
            for launch in launches:
                if launch.status == 1 and launch.netstamp > 0:
                    current_time = datetime.utcnow()
                    launch_time = datetime.utcfromtimestamp(int(launch.netstamp))
                    if (launch_time - current_time).total_seconds() < 86400:
                        todays_launches.append(launch)
            self.send_daily_to_twitter(todays_launches)
        else:
            logger.error(response.status_code + ' ' + response)

    def check_launch_weekly(self):
        launch_data = self.launchLibrary.get_next_launches().json()['launches']
        logger.info(launch_data)

    def send_daily_to_twitter(self, launches):
        logger.info("Size %s" % launches)
        header = "Daily Digest %s:" % datetime.strftime(datetime.now(), "%-m/%d")
        if len(launches) == 0:
            message = "%s There are currently no launches confirmed Go for Launch within the next 24 hours." % header
            self.send_twitter_update(message)
        if len(launches) == 1:
            launch = launches[0]
            current_time = datetime.utcnow()
            launch_time = datetime.utcfromtimestamp(int(launch.netstamp))
            message = "%s %s launching from %s in %s hours." % (header, launch.name, launch.location_name, '{0:g}'.format(float(round(abs(launch_time - current_time).total_seconds() / 3600.0))))
            self.send_twitter_update(message)

            update_notification_record(launch)
        if len(launches) > 1:
            message = "%s There are %i confirmed launches within the next 24 hours...(1/%i)" % (header,
                                                                                                len(launches),
                                                                                                len(launches) + 1)
            self.send_twitter_update(message)
            for index, launch in enumerate(launches, start=1):
                current_time = datetime.utcnow()
                launch_time = datetime.utcfromtimestamp(int(launch.netstamp))
                message = "%s launching from %s in %s hours. (%i/%i)" % (launch.name,
                                                                         launch.location.name,
                                                                         '{0:g}'.format(float(
                                                                             round(abs(
                                                                                 launch_time - current_time)
                                                                                   .total_seconds() / 3600.0))),
                                                                         index + 1, len(launches) + 1)
                self.send_twitter_update(message)
                update_notification_record(launch)

    def send_twitter_update(self, message):
        try:
            if len(message) > 120:
                end = message[-5:]
                if re.search("([1-9]*/[1-9])", end):
                    message = (message[:111] + '... ' + end)
                else:
                    message = (message[:117] + '...')
            logger.info(message + " | " + str(len(message)))
            # self.twitter.statuses.update(status=message)
        except TwitterHTTPError as e:
            logger.error("%s %s" % (str(e), message))
