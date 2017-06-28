from datetime import timedelta
import pdb
import re
import logging
from django.utils.datetime_safe import datetime, time
from twitter import Twitter, OAuth, TwitterHTTPError
from bot.libraries.launchlibrarysdk import LaunchLibrarySDK
from bot.libraries.onesignalsdk import OneSignalSdk
from bot.models import Notification
from bot.utils.config import keys
from bot.utils.deserializer import json_to_model

# import the logging library

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
    if any((datetime.now() - notification.last_daily_digest_post).total_seconds() < 80000
           for notification in notifications):
        return False
    else:
        return True


class DailyDigestServer:
    def __init__(self, debug=None, version=None):
        self.one_signal = OneSignalSdk(AUTH_TOKEN_HERE, APP_ID)
        if version is None:
            version = '1.2.1'
        self.launchLibrary = LaunchLibrarySDK(version=version)
        if debug is None:
            self.DEBUG = False
        else:
            self.DEBUG = debug
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
        if daily:
            if daily_allowed():
                self.check_launch_daily()
            else:
                logger.info("Daily already ran, skipping.")
        elif weekly:
            self.check_launch_weekly()
        else:
            logger.error("Both daily and weekly false...ignoring request.")

    def get_next_launches(self):
        logger.info("Daily Digest running...")
        response = self.launchLibrary.get_next_launches()
        if response.status_code is 200:
            response_json = response.json()
            launch_data = response_json['launches']
            logger.info("Found %i launches." % len(launch_data))
            launches = []
            for launch in launch_data:
                launch = json_to_model(launch)
                launches.append(launch)
            return launches
        else:
            logger.error(response.status_code + ' ' + response)

    def get_next_weeks_launches(self):
        logger.info("Weekly Digest running...")
        response = self.launchLibrary.get_next_weeks_launches()
        if response.status_code is 200:
            response_json = response.json()
            launch_data = response_json['launches']
            logger.info("Found %i launches." % len(launch_data))
            launches = []
            for launch in launch_data:
                launch = json_to_model(launch)
                launches.append(launch)
            return launches
        else:
            logger.error(response.status_code + ' ' + response)

    def check_launch_daily(self):
        todays_launches = []
        for launch in self.get_next_launches():
            if launch.status == 1 and launch.netstamp > 0:
                current_time = datetime.utcnow()
                launch_time = datetime.utcfromtimestamp(int(launch.netstamp))
                if (launch_time - current_time).total_seconds() < 86400:
                    todays_launches.append(launch)
        self.send_daily_to_twitter(todays_launches)

    def check_launch_weekly(self):
        this_weeks_confirmed_launches = []
        this_weeks_possible_launches = []
        for launch in self.get_next_weeks_launches():
            update_notification_record(launch)
            if launch.location_name is None:
                launch.location_name = 'Unknown'
            if launch.status == 1 and launch.netstamp > 0:
                this_weeks_confirmed_launches.append(launch)
            elif launch.status == 0 or launch.netstamp == 0:
                this_weeks_possible_launches.append(launch)
        self.send_weekly_to_twitter(this_weeks_possible_launches, this_weeks_confirmed_launches)

    def send_weekly_to_twitter(self, possible, confirmed):
        logger.info("Total launches found - %s" % (len(possible) + len(confirmed)))
        full_header = "This Week in SpaceFlight:"
        compact_header = "TWSF:"
        total = (len(possible) + len(confirmed))

        # First, send out a summary.
        if total == 0:
            message = "%s There are no launches scheduled this week." % full_header
            self.send_twitter_update(message)
        elif len(confirmed) == 1 and len(possible) == 1:
            message = "%s There is one confirmed launch with one other possible this week." % full_header
            self.send_twitter_update(message)
        elif len(confirmed) == 0 and len(possible) == 1:
            message = "%s There is one possible launch this week." % full_header
            self.send_twitter_update(message)
        elif len(confirmed) == 1 and len(possible) == 0:
            message = "%s There is one confirmed launch this week." % full_header
            self.send_twitter_update(message)
        elif len(confirmed) > 1 and len(possible) == 1:
            message = "%s There are %s launches confirmed with one other possible this week." % (full_header,
                                                                                                 len(confirmed))
            self.send_twitter_update(message)
        elif len(confirmed) == 1 and len(possible) > 1:
            message = "%s There is one launch confirmed with %s other possible this week." % (full_header,
                                                                                              len(possible))
            self.send_twitter_update(message)
        elif confirmed > 0 and len(possible) == 0:
            message = "%s There are %s confirmed launches scheduled this week." % (full_header, len(confirmed))
            self.send_twitter_update(message)
        elif confirmed == 0 and len(possible) > 0:
            message = "%s There are %s possible launches scheduled this week." % (full_header, len(possible))
            self.send_twitter_update(message)

        if len(confirmed) == 1:
            launch = confirmed[0]
            day = datetime.fromtimestamp(int(launch.netstamp)).strftime("%A")
            message = "%s %s launching from %s on %s. (1/%i)" % (compact_header, launch.name, launch.location_name, day,
                                                                 total)
            self.send_twitter_update(message)
        elif len(confirmed) > 1:
            for index, launch in enumerate(confirmed, start=1):
                if len(launch.location_name) > 10:
                    location_name = launch.location_name.split(", ")[0]
                else:
                    location_name = launch.location_name
                message = "%s %s launching from %s on %s. (%i/%i)" % (compact_header, launch.name,
                                                                      location_name,
                                                                      datetime
                                                                      .fromtimestamp(int(launch.netstamp))
                                                                      .strftime("%A"),
                                                                      index,
                                                                      total)
                self.send_twitter_update(message)
        if len(possible) == 1:
            launch = possible[0]
            message = "%s %s might launch this week from %s. (%i/%i)" % (compact_header, launch.name,
                                                                         launch.location_name,
                                                                         len(confirmed) + 1, total)
            self.send_twitter_update(message)
        elif len(possible) > 1:
            for index, launch in enumerate(possible, start=1):
                if len(launch.location_name) > 10:
                    location_name = launch.location_name.split(", ")[0]
                else:
                    location_name = launch.location_name
                message = "%s %s might be launching from %s. (%i/%i)" % (compact_header,
                                                                         launch.name,
                                                                         location_name,
                                                                         index + len(confirmed),
                                                                         total)
                self.send_twitter_update(message)

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
            message = "%s %s launching from %s in %s hours." % (header, launch.name, launch.location_name,
                                                                '{0:g}'.format(float(round(abs(
                                                                    launch_time - current_time)
                                                                                           .total_seconds() / 3600.0))))
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
            if message.endswith(' (1/1)'):
                message = message[:-6]
            if len(message) > 120:
                end = message[-5:]
                if re.search("([1-9]*/[1-9])", end):
                    message = (message[:111] + '... ' + end)
                else:
                    message = (message[:117] + '...')
            logger.info('Sending to Twitter | %s | %s' % (message, str(len(message))))
            if not self.DEBUG:
                self.twitter.statuses.update(status=message)
        except TwitterHTTPError as e:
            logger.error("%s %s" % (str(e), message))
