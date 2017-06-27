import logging
import pdb
from django.utils.datetime_safe import datetime
from bot.libraries.launchlibrarysdk import LaunchLibrarySDK
from bot.libraries.onesignalsdk import OneSignalSdk
from bot.utils.config import keys
from bot.models import Notification
from bot.utils.deserializer import json_to_model
from bot.utils.util import seconds_to_time

AUTH_TOKEN_HERE = keys['AUTH_TOKEN_HERE']
APP_ID = keys['APP_ID']
DAEMON_SLEEP = 600
TAG = 'Notification Server'

# Get an instance of a logger
logger = logging.getLogger('bot')


class NotificationServer:
    def __init__(self):
        self.onesignal = OneSignalSdk(AUTH_TOKEN_HERE, APP_ID)
        self.launchLibrary = LaunchLibrarySDK(version='dev')
        response = self.onesignal.get_app(APP_ID)
        assert response.status_code == 200
        self.app = response.json()
        self.app_auth_key = self.app['basic_auth_key']
        assert isinstance(self.app, dict)
        assert self.app['id'] and self.app['name'] and self.app['updated_at'] and self.app['created_at']

    def send_to_twitter(self, message, notification):
        # Need to add actual twitter post here.
        logger.info(message)

        notification.last_twitter_post = datetime.now()
        notification.last_net_stamp = notification.launch.netstamp
        notification.last_net_stamp_timestamp = datetime.now()
        logger.info('Updating Notification %s to timestamp %s' % (notification.launch.id,
                                                                  notification.last_daily_digest_post
                                                                  .strftime("%A %d. %B %Y")))

        notification.save()

    def get_next_launches(self):
        logger.info("Getting next launches...")
        response = self.launchLibrary.get_next_launches()
        if response.status_code is 200:
            response_json = response.json()
            launch_data = response_json['launches']
            launches = []
            for launch in launch_data:
                launch = json_to_model(launch)
                launches.append(launch)
            return launches
        else:
            logger.error(response.status_code + ' ' + response)

    def check_next_launch(self):
        # Now that we have models loop through to find launches.
        for launch in self.get_next_launches():
            if launch.netstamp > 0:
                current_time = datetime.utcnow()
                launch_time = datetime.utcfromtimestamp(int(launch.netstamp))
                if current_time <= launch_time:
                    diff = int((launch_time - current_time).total_seconds())
                    logger.info('%s in %s seconds' % (launch.name, diff))
                    self.check_launch_window(diff, launch)

    def netstamp_changed(self, notification, diff):
        if diff <= 86400:
            if diff >= 3600:
                self.send_to_twitter('SCHEDULE UPDATE: %s launching from %s in %s' %
                                     (notification.launch_name, notification.launch.location_name,
                                      seconds_to_time(diff)),
                                     notification)
            if diff <= 3600:
                self.send_to_twitter('SCHEDULE UPDATE: %s launching from %s in %s' %
                                     (notification.launch_name, notification.launch.location_name,
                                      seconds_to_time(diff)),
                                     notification)

    def check_twitter(self, diff, launch):
        notification = Notification.objects.get(launch=launch)
        pdb.set_trace()
        if (notification.last_net_stamp - launch.netstamp) > 600 and diff <= 259200:
            self.netstamp_changed(notification)
        elif diff <= 86400:
            if notification.last_twitter_post is not None:
                time_since_digest = (datetime.now() - notification.last_daily_digest_post).total_seconds()
                time_since_twitter = (datetime.now() - notification.last_twitter_post).total_seconds()
                time_since_last_twitter_update = min(time_since_digest, time_since_twitter)
                logger.info('Seconds since last update on Twitter %d for %s' % (time_since_last_twitter_update,
                                                                                launch.name))

                if diff >= 3600:
                    if time_since_last_twitter_update >= 43200:
                        self.send_to_twitter('%s launching from %s in %s' %
                                             (launch.name, launch.location_name, seconds_to_time(diff)),
                                             notification)
                if diff <= 3600:
                    if time_since_last_twitter_update >= 43200:
                        self.send_to_twitter('%s launching from %s in %s' %
                                             (launch.name, launch.location_name, seconds_to_time(diff)),
                                             notification)

            else:
                logger.info('%s has not been posted to Twitter.' % launch.name)
                self.send_to_twitter('%s launching from %s in %s' % (launch.name, launch.location_name,
                                                                     seconds_to_time(diff)), notification)

    def check_launch_window(self, diff, launch):
        self.check_twitter(diff, launch)
        notification = Notification.objects.get(launch=launch)

        # If launch is within 24 hours...
        if 86400 >= diff > 3600 and not notification.wasNotifiedTwentyFourHour:
            self.send_notification(launch)
            notification.is_notified_24(True)
        elif 3600 >= diff > 600 and not notification.wasNotifiedOneHour:
            self.send_notification(launch)
            notification.is_notified_one_hour(True)
        elif diff <= 600 and not notification.wasNotifiedTenMinutes:
            self.send_notification(launch)
            notification.is_notified_ten_minutes(True)
        notification.save()

    def send_notification(self, launch):
        self.onesignal.user_auth_key = self.app_auth_key
        self.onesignal.app_id = APP_ID
        logger.info('Creating notification for %s' % launch.launch_name)

        # Create a notification
        contents = '%s launching from %s' % (launch.launch_name, launch.location['name'])
        kwargs = dict(
            content_available=True,
            included_segments=['Debug'],
            isAndroid=True,
            data={"silent": True}
        )
        url = 'https://launchlibrary.net'
        heading = 'Space Launch Now'
        response = self.onesignal.create_notification(contents, heading, url, **kwargs)
        assert response.status_code == 200

        notification_data = response.json()
        notification_id = notification_data['id']
        assert notification_data['id'] and notification_data['recipients']

        # Get the notification
        response = self.onesignal.get_notification(APP_ID, notification_id, self.app_auth_key)
        notification_data = response.json()
        assert notification_data['id'] == notification_id
        assert notification_data['contents']['en'] == contents

    def run(self):
        """The daemon's main loop for doing work"""
        self.check_next_launch()
