import time

import datetime

import re
from bot.models import Launch, Location
from bot.serializer import LaunchSerializer
from twitter import *
from bot.libraries.launchlibrarysdk import LaunchLibrarySDK
from bot.libraries.onesignalsdk import OneSignalSdk
from bot.utils.config import keys
from bot.utils.util import log, log_error

AUTH_TOKEN_HERE = keys['AUTH_TOKEN_HERE']
APP_ID = keys['APP_ID']
DAEMON_SLEEP = 6000
TAG = 'Digest Server'


def run_daily():
    log(TAG, 'Running Daily Digest - Daily...')
    daily_digest = DailyDigestServer()
    daily_digest.run(daily=True)


def run_weekly():
    log(TAG, 'Running Daily Digest - Weekly...')
    daily_digest = DailyDigestServer()
    daily_digest.run(weekly=True)


class DailyDigestServer:
    def __init__(self):
        self.one_signal = OneSignalSdk(AUTH_TOKEN_HERE, APP_ID)
        self.launchLibrary = LaunchLibrarySDK()
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
        if daily:
            self.check_launch_daily()
        if weekly:
            self.check_launch_weekly()

    def check_launch_daily(self):
        response = self.launchLibrary.get_next_launches()
        response_json = response.json()
        launch_data = response_json['launches']
        launches = []
        for launch in launch_data:
            serializer = LaunchSerializer(data=launch)
            if serializer.is_valid():
                launch = serializer.save()[0]
                launches.append(launch)
            else:
                log_error(TAG, serializer.errors)
        todays_launches = []
        for launch in launches:
            if launch.status == 1 and launch.netstamp > 0:
                current_time = datetime.datetime.utcnow()
                launch_time = datetime.datetime.utcfromtimestamp(int(launch.netstamp))
                if (launch_time - current_time).total_seconds() < 86400:
                    todays_launches.append(launch)
        self.send_daily_to_twitter(todays_launches)

    def check_launch_weekly(self):
        launch_data = self.launchLibrary.get_next_launches().json()['launches']
        log(TAG, launch_data)

    def send_daily_to_twitter(self, launches):
        log(TAG, "Size %s" % launches)
        header = "Daily Digest %s:" % time.strftime("%-m/%d")
        if len(launches) == 0:
            message = "%s There are currently no launches confirmed Go for Launch within the next 24 hours." % header
            self.send_twitter_update(message)
        if len(launches) == 1:
            launch = launches[0]
            current_time = datetime.datetime.utcnow()
            launch_time = datetime.datetime.utcfromtimestamp(int(launch.netstamp))
            message = "%s %s launching from %s in %s hours." % (header, launch.name, launch.location.name,
                                                                '{0:g}'.format(float(round(abs
                                                                                           (launch_time - current_time)
                                                                                           .total_seconds() / 3600.0))))
            self.send_twitter_update(message)
        if len(launches) > 1:
            message = "%s There are %i confirmed launches within the next 24 hours...(1/%i)" % (header,
                                                                                                len(launches),
                                                                                                len(launches) + 1)
            self.send_twitter_update(message)
            for index, launch in enumerate(launches, start=1):
                current_time = datetime.datetime.utcnow()
                launch_time = datetime.datetime.utcfromtimestamp(int(launch.netstamp))
                message = "%s launching from %s in %s hours. (%i/%i)" % (launch.name,
                                                                         launch.location.name,
                                                                         '{0:g}'.format(float(
                                                                             round(abs(
                                                                                 launch_time - current_time)
                                                                                   .total_seconds() / 3600.0))),
                                                                         index + 1, len(launches) + 1)
                self.send_twitter_update(message)

    def send_twitter_update(self, message):
        try:
            if len(message) > 120:
                end = message[-5:]
                if re.search("([1-9]*/[1-9])", end):
                    message = (message[:111] + '... ' + end)
                else:
                    message = (message[:117] + '...')
            log(TAG, message + " | " + str(len(message)))
            # self.twitter.statuses.update(status=message)
        except TwitterHTTPError as e:
            log_error(TAG, str(e) + " - " + message)
