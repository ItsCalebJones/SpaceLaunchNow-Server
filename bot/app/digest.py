import json
import os
import urllib
from datetime import timedelta
from django.core import serializers

import requests
from djcelery.tests.req import RequestFactory
from num2words import num2words
import re
import logging
from django.utils.datetime_safe import datetime, time
import pytz
from rest_framework.renderers import JSONRenderer
from twitter import Twitter, OAuth, TwitterHTTPError
from bot.libraries.launchlibrarysdk import LaunchLibrarySDK
from bot.libraries.onesignalsdk import OneSignalSdk
from bot.models import Notification, DailyDigestRecord
from bot.serializer import LaunchSerializer
from bot.utils.config import keys
from bot.utils.deserializer import launch_json_to_model
# import the logging library

# Get an instance of a logger
logger = logging.getLogger('bot.digest')

AUTH_TOKEN_HERE = keys['AUTH_TOKEN_HERE']
APP_ID = keys['APP_ID']
DAEMON_SLEEP = 6000


def update_notification_record(launch):
    notification = Notification.objects.get(launch=launch)
    notification.last_net_stamp = launch.netstamp
    notification.last_net_stamp_timestamp = datetime.now()
    logger.info('Updating Notification %s to timestamp %s' % (notification.launch.name,
                                                              datetime.fromtimestamp(notification.launch.netstamp)
                                                              .strftime("%A %d %B %Y")))
    notification.save()


def create_daily_digest_record(total, messages, launches):
    data = []

    for launch in launches:
        launch_json = serializers.serialize('json', [launch, ])
        data.append(launch_json)
    DailyDigestRecord.objects.create(timestamp=datetime.now(),
                                     messages=messages,
                                     count=total,
                                     data=data)


class DigestServer:
    def __init__(self, debug=None, version=None):
        self.one_signal = OneSignalSdk(AUTH_TOKEN_HERE, APP_ID)
        if version is None:
            version = '1.3'
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
        self.twitter_upload = Twitter(domain='upload.twitter.com',
                                      auth=OAuth(keys['TOKEN_KEY'], keys['TOKEN_SECRET'], keys['CONSUMER_KEY'],
                                                 keys['CONSUMER_SECRET'])
                                      )
        self.time_to_next_launch = None
        self.next_launch = None

    def run(self, daily=False, weekly=False):
        if daily:
            self.check_launch_daily()
        elif weekly:
            self.check_launch_weekly()
        else:
            logger.error("Both daily and weekly false...ignoring request.")

    def get_next_launches(self):
        logger.info("Daily Digest running...")
        response = self.launchLibrary.get_next_launch(count=5)
        if response.status_code is 200:
            response_json = response.json()
            launch_data = response_json['launches']
            logger.info("Found %i launches" % len(launch_data))
            logger.debug("DATA: %s" % launch_data)
            launches = []
            for launch in launch_data:
                launch = launch_json_to_model(launch)
                launch.save()
                launches.append(launch)
            return launches
        else:
            logger.error(response.status_code + ' ' + response)

    def get_next_launch(self):
        response = self.launchLibrary.get_next_launch()
        if response.status_code is 200:
            response_json = response.json()
            launch_data = response_json['launches']
            logger.info("Found %i launches" % len(launch_data))
            logger.debug("DATA: %s" % launch_data)
            for launch in launch_data:
                return launch_json_to_model(launch)
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
                launch = launch_json_to_model(launch)
                launch.save()
                launches.append(launch)
            return launches
        else:
            logger.error(str(response.status_code) + ' ' + response.text)

    def check_launch_daily(self):
        confirmed_launches = []
        possible_launches = []
        current_time = datetime.utcnow()
        for launch in self.get_next_launches():
            update_notification_record(launch)
            if launch.netstamp > 0 and (datetime.utcfromtimestamp(int(launch.netstamp)) - current_time) \
                    .total_seconds() < 172800:
                if launch.status == 1:
                    confirmed_launches.append(launch)
                elif launch.status == 2:
                    possible_launches.append(launch)
        self.send_daily_to_twitter(possible=possible_launches, confirmed=confirmed_launches)

    def check_launch_weekly(self):
        this_weeks_confirmed_launches = []
        this_weeks_possible_launches = []
        try:
            for launch in self.get_next_weeks_launches():
                update_notification_record(launch)
                if launch.status == 1 and launch.netstamp > 0:
                    this_weeks_confirmed_launches.append(launch)
                elif launch.status == 0 or launch.netstamp == 0:
                    this_weeks_possible_launches.append(launch)
            self.send_weekly_to_twitter(this_weeks_possible_launches, this_weeks_confirmed_launches)
        except TypeError as e:
            logger.error(e)

    def send_weekly_to_twitter(self, possible, confirmed):
        logger.info("Total launches found - confirmed: %s possible: %s" % (len(confirmed), len(possible)))
        full_header = "This Week in SpaceFlight:"
        compact_header = "TWSF:"
        total = (len(possible) + len(confirmed))

        # First, send out a summary.
        if total == 0:
            message = "%s There are no launches scheduled this week. Follow along with schedule updates at" \
                      " https://spacelaunchnow.me/launches/" % full_header
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
                                                                                                 num2words(
                                                                                                     len(confirmed)))
            self.send_twitter_update(message)
        elif len(confirmed) == 1 and len(possible) > 1:
            message = "%s There is one launch confirmed with %s other possible this week." % (full_header,
                                                                                              num2words(len(possible)))
            self.send_twitter_update(message)
        elif len(confirmed) > 0 and len(possible) == 0:
            message = "%s There are %s confirmed launches scheduled this week." % (full_header,
                                                                                   num2words(len(confirmed)))
            self.send_twitter_update(message)
        elif len(confirmed) == 0 and len(possible) > 0:
            message = "%s There are %s possible launches scheduled this week." % (full_header,
                                                                                  num2words(len(possible)))
            self.send_twitter_update(message)

        if len(confirmed) == 1:
            launch = confirmed[0]
            day = datetime.fromtimestamp(int(launch.netstamp)).replace(tzinfo=pytz.UTC).strftime("%A")
            message = "%s %s launching from %s on %s. (1/%i)" % (
                compact_header, launch.name, launch.location_set.all()[0].name, day,
                total)
            if launch.img_url is not None and launch.img_url is not '':
                self.send_twitter_update(message)
            else:
                self.send_twitter_update(message)
        elif len(confirmed) > 1:
            for index, launch in enumerate(confirmed, start=1):
                message = "%s %s launching from %s on %s. (%i/%i)" % (compact_header, launch.name,
                                                                      launch.location_set.all()[0].name,
                                                                      datetime
                                                                      .fromtimestamp(int(launch.netstamp))
                                                                      .replace(tzinfo=pytz.UTC)
                                                                      .strftime("%A"),
                                                                      index,
                                                                      total)
                if launch.img_url is not None and launch.img_url is not '':
                    self.send_twitter_update(message)
                else:
                    self.send_twitter_update(message)
        if len(possible) == 1:
            launch = possible[0]
            message = "%s %s might launch this week from %s. (%i/%i)" % (compact_header, launch.name,
                                                                         launch.location_set.all()[0].name,
                                                                         len(confirmed) + 1, total)
            if launch.img_url is not None and launch.img_url is not '':
                self.send_twitter_update(message)
            else:
                self.send_twitter_update(message)
        elif len(possible) > 1:
            for index, launch in enumerate(possible, start=1):
                message = "%s %s might be launching from %s. (%i/%i)" % (compact_header,
                                                                         launch.name,
                                                                         launch.location_set.all()[0].name,
                                                                         index + len(confirmed),
                                                                         total)
                if launch.img_url is not None and launch.img_url is not '':
                    self.send_twitter_update(message)
                else:
                    self.send_twitter_update(message)

    def send_daily_to_twitter(self, possible, confirmed):
        logger.debug("Confirmed count - %s | Possible Count - %s" % (len(confirmed), len(possible)))
        header = "Daily Digest %s:" % datetime.strftime(datetime.now(), "%m/%d")
        messages = "MESSAGES SENT TO TWITTER: \n"
        if len(confirmed) == 0 and len(possible) == 0:
            logger.info("No launches - sending message. ")

            message = "%s There are currently no launches scheduled within the next 48 hours." % header

            messages = messages + message + "\n"
            self.send_twitter_update(message)

        if len(confirmed) == 1 and len(possible) == 0:
            launch = confirmed[0]

            current_time = datetime.utcnow()
            launch_time = datetime.utcfromtimestamp(int(launch.netstamp))
            logger.info("One launch - sending message. ")
            message = "%s %s launching from %s in %s hours. \n %s" % (
                header, launch.name, launch.location_set.all()[0].name,
                '{0:g}'.format(float(round(abs(launch_time - current_time).total_seconds() / 3600.0))),
                'https://spacelaunchnow.me/launch/%s' % launch.id)
            messages = messages + message + "\n"
            if launch.img_url is not None and launch.img_url is not '':
                self.send_twitter_update(message)
            else:
                self.send_twitter_update(message)

        if len(confirmed) == 0 and len(possible) == 1:
            launch = possible[0]

            logger.info("One launch - sending message. ")
            date = datetime.utcfromtimestamp(launch.netstamp).replace(tzinfo=pytz.UTC)
            message = "%s %s might be launching from %s on %s." % (
                header, launch.name, launch.location_set.all()[0].name,
                date.strftime("%A at %H:%S %Z"))
            messages = messages + message + "\n"
            if launch.img_url is not None and launch.img_url is not '':
                self.send_twitter_update(message)
            else:
                self.send_twitter_update(message)

        if len(confirmed) == 1 and len(possible) == 1:
            possible_launch = possible[0]
            confirmed_launch = confirmed[0]

            logger.info("One launch possible - sending message. ")
            date = datetime.utcfromtimestamp(possible_launch.netstamp).replace(tzinfo=pytz.UTC)
            message = "%s %s might be launching from %s on %s." % (header, possible_launch.name,
                                                                   possible_launch.location_set.all()[0].name,
                                                                   date.strftime("%A at %H:%S %Z"))
            messages = messages + message + "\n"
            if possible_launch.img_url is not None and possible_launch.img_url is not '':
                self.send_twitter_update(message)
            else:
                self.send_twitter_update(message)

            current_time = datetime.utcnow()
            launch_time = datetime.utcfromtimestamp(int(confirmed_launch.netstamp))
            logger.info("One launch confirmed - sending message. ")
            message = "%s %s launching from %s in %s hours. \n %s" % (
                header, confirmed_launch.name, confirmed_launch.location_set.all()[0].name,
                '{0:g}'.format(float(round(abs(launch_time - current_time).total_seconds() / 3600.0))),
                'https://spacelaunchnow.me/launch/%s' % launch.id)
            messages = messages + message + "\n"
            if confirmed_launch.img_url is not None and confirmed_launch.img_url is not '':
                self.send_twitter_update(message)
            else:
                self.send_twitter_update(message)

        if len(confirmed) > 1 and len(possible) == 0:
            logger.info("More then one launch - sending summary first. ")
            message = "%s There are %i confirmed launches within the next 48 hours...(1/%i)" % (header,
                                                                                                len(confirmed),
                                                                                                len(confirmed) + 1)
            messages = messages + message + "\n"
            self.send_twitter_update(message)
            for index, launch in enumerate(confirmed, start=1):
                current_time = datetime.utcnow()

                launch_time = datetime.utcfromtimestamp(int(launch.netstamp))
                message = "%s launching from %s in %s hours. (%i/%i) \n %s" % (
                    launch.name,
                    launch.location_set.all()[0].name,
                    '{0:g}'.format(float(round(abs(launch_time - current_time).total_seconds() / 3600.0))),
                    index + 1, len(confirmed) + 1,
                    'https://spacelaunchnow.me/launch/%s' % launch.id)
                messages = messages + message + "\n"
                if launch.img_url is not None:
                    self.send_twitter_update(message)
                else:
                    self.send_twitter_update(message)

        if len(confirmed) == 0 and len(possible) > 1:
            logger.info("More then one launch - sending summary first. ")
            message = "%s There are %s possible launches within the next 48 hours...(1/%i)" % (header,
                                                                                               num2words(len(possible)),
                                                                                               len(possible) + 1)
            messages = messages + message + "\n"
            self.send_twitter_update(message)
            for index, launch in enumerate(possible, start=1):
                date = datetime.utcfromtimestamp(launch.netstamp).replace(tzinfo=pytz.UTC)
                message = "%s might be launching from %s on %s. (%i/%i)" % (launch.name,
                                                                            launch.location_set.all()[0].name,
                                                                            date.strftime("%A at %H:%S %Z"),
                                                                            index + 1, len(possible) + 1)
                messages = messages + message + "\n"
                if launch.img_url is not None and launch.img_url is not '':
                    self.send_twitter_update(message)
                else:
                    self.send_twitter_update(message)

        if len(confirmed) > 1 and len(possible) > 1:
            total = confirmed + possible
            logger.info("More then one launch - sending summary first. ")
            message = "%s There are %i possible and %i confirmed launches within the next 48 hours." % (header,
                                                                                                        num2words(len(
                                                                                                            possible)),
                                                                                                        num2words(len(
                                                                                                            confirmed)))
            messages = messages + message + "\n"
            self.send_twitter_update(message)

            # Possible launches
            for index, launch in enumerate(possible, start=1):
                message = "%s might be launching from %s on %s. (%i/%i)" % (launch.name,
                                                                            launch.location_set.all()[0].name,
                                                                            datetime.fromtimestamp(launch
                                                                                                   .launch.netstamp)
                                                                            .strftime("%A at %H:%S %Z"),
                                                                            index, len(total))
                messages = messages + message + "\n"
                if launch.img_url is not None and launch.img_url is not '':
                    self.send_twitter_update(message)
                else:
                    self.send_twitter_update(message)

            # Confirmed launches
            for index, launch in enumerate(confirmed, start=1):
                current_time = datetime.utcnow()

                launch_time = datetime.utcfromtimestamp(int(launch.netstamp))
                message = "%s launching from %s in %s hours. (%i/%i) \n %s" % (
                    launch.name,
                    launch.location_set.all()[0].name,
                    '{0:g}'.format(float(round(abs(launch_time - current_time).total_seconds() / 3600.0))),
                    possible + index, len(total), 'https://spacelaunchnow.me/launch/%s' % launch.id)
                messages = messages + message + "\n"
                if launch.img_url is not None and launch.img_url is not '':
                    self.send_twitter_update(message)
                else:
                    self.send_twitter_update(message)

        create_daily_digest_record(len(confirmed) + len(possible), messages, confirmed + possible)

    def send_twitter_update(self, message):
        try:
            if message.endswith(' (1/1)'):
                message = message[:-6]
            if len(message) > 280:
                end = message[-5:]

                if re.search("([1-9]*/[1-9])", end):
                    message = (message[:271] + '... ' + end)
                else:
                    message = (message[:277] + '...')
            logger.info('Sending to Twitter | %s | %s | DEBUG %s' % (message, str(len(message)), self.DEBUG))
            if not self.DEBUG:
                logger.debug('Sending to twitter - message: %s' % message)
                self.twitter.statuses.update(status=message)
        except TwitterHTTPError as e:
            logger.error("%s %s" % (str(e), message))
