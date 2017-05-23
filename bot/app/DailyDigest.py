import time

import datetime

import re
from apscheduler.schedulers.background import BackgroundScheduler
from bot.libraries.launchlibrarysdk import LaunchLibrarySDK
from bot.libraries.onesignalsdk import OneSignalSdk
from bot.models import Launch
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
        launch_data = self.launchLibrary.get_next_launches().json()['launches']
        launches = []
        for launch_instance in launch_data:
            launch = Launch(launch_instance)
            if launch.status == 1 and launch.net_stamp > 0:
                current_time = datetime.datetime.utcnow()
                launch_time = datetime.datetime.utcfromtimestamp(int(launch.net_stamp))
                if (launch_time - current_time).total_seconds() < 86400:
                    launches.append(launch)
        self.send_daily_to_twitter(launches)

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
            launch_time = datetime.datetime.utcfromtimestamp(int(launch.net_stamp))
            message = "%s %s launching from %s in %s hours." % (header, launch.launch_name, launch.location['name'],
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
                launch_time = datetime.datetime.utcfromtimestamp(int(launch.net_stamp))
                message = "%s launching from %s in %s hours. (%i/%i)" % (launch.launch_name,
                                                                         launch.location['name'],
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
            self.twitter.statuses.update(status=message)
        except TwitterHTTPError as e:
            log_error(TAG, str(e) + " - " + message)