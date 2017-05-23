import datetime


from libraries.launchlibrarysdk import LaunchLibrarySDK
from libraries.onesignalsdk import OneSignalSdk

from bot.models import Launch
from bot.utils.util import log, seconds_to_time

DAEMON_SLEEP = 600
TAG = 'Notification Server'


class NotificationServer:
    def __init__(self, scheduler):
        self.onesignal = OneSignalSdk(AUTH_TOKEN_HERE, APP_ID)
        self.launchLibrary = LaunchLibrarySDK()
        response = self.onesignal.get_app(APP_ID)
        assert response.status_code == 200
        self.app = response.json()
        assert isinstance(self.app, dict)
        assert self.app['id'] and self.app['name'] and self.app['updated_at'] and self.app['created_at']
        self.time_to_next_launch = None
        self.next_launch = None
        self.scheduler = scheduler

    def send_to_twitter(self, message, launch):
        log(TAG, message)

    def check_next_launch(self):
        response = self.launchLibrary.get_next_launches()
        launch_data = response.json()
        if response.status_code is 200:
            log(TAG, "Found %i launches." % len(launch_data["launches"]))
            for launches in launch_data["launches"]:
                launch = Launch(launches)
                log(TAG, launch.launch_name)
                if launch.net_stamp > 0:
                    current_time = datetime.datetime.utcnow()
                    launch_time = datetime.datetime.utcfromtimestamp(int(launch.net_stamp))
                    if current_time <= launch_time:
                        diff = int((launch_time - current_time).total_seconds())
                        if self.time_to_next_launch is None:
                            self.time_to_next_launch = diff
                            self.next_launch = launch
                        elif diff < self.time_to_next_launch:
                            self.time_to_next_launch = diff
                            self.next_launch = launch
                        self.check_launch_window(diff, launch)
        else:
            log(TAG, response)

    def check_twitter(self, diff, launch):
        if launch.last_twitter_post is not None:
            time_since_last_twitter_update = (datetime.datetime.utcnow() - datetime.datetime.utcfromtimestamp(
                int(launch.last_twitter_post))).total_seconds()
            log(TAG, 'Seconds since last update on Twitter %d for %s' % (time_since_last_twitter_update, launch.launch_name))
            if diff < 86400:
                if diff > 3600:
                    if time_since_last_twitter_update > 43200:
                        self.send_to_twitter('%s launching from %s in %s' %
                                             (launch.launch_name, launch.location['name'], seconds_to_time(diff)),
                                             launch)
                if diff < 3600:
                    if time_since_last_twitter_update > 3600:
                        self.send_to_twitter('%s launching from %s in %s' %
                                             (launch.launch_name, launch.location['name'], seconds_to_time(diff)),
                                             launch)
        else:
            log(TAG, '%s has not been posted to Twitter.' % launch.launch_name)
            self.send_to_twitter('%s launching from %s in %s' % (launch.launch_name, launch.location['name'],
                                                                 seconds_to_time(diff)), launch)

    def check_launch_window(self, diff, launch):
        self.check_twitter(diff, launch)

        # If launch is within 24 hours...
        if 86400 >= diff > 3600 and not launch.wasNotifiedTwentyFourHour:
            self.send_notification(launch)
            launch.is_notified_24(True)
        elif 3600 >= diff > 600 and not launch.wasNotifiedOneHour:
            self.send_notification(launch)
            launch.is_notified_one_hour(True)
        elif diff <= 600 and not launch.wasNotifiedTenMinutes:
            self.send_notification(launch)
            launch.is_notified_ten_minutes(True)

    def send_notification(self, launch):
        self.onesignal.user_auth_key = self.app_auth_key
        self.onesignal.app_id = APP_ID
        log(TAG, 'Creating notification for %s' % launch.launch_name)

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
        if self.time_to_next_launch > 600:
            log(TAG, 'Next launch %s in %i hours, sleeping for %d seconds.' % (self.next_launch.launch_name,
                                                                               self.time_to_next_launch / 3600,
                                                                               DAEMON_SLEEP))
            self.scheduler.add_job(self.run, 'date',
                                   run_date=datetime.datetime.now() + datetime.timedelta(seconds=DAEMON_SLEEP))
        elif self.time_to_next_launch is not None and self.time_to_next_launch > 0:
            log(TAG, 'Next launch %s is imminent, sleeping for %d seconds.' % (self.time_to_next_launch / 3600,
                                                                               self.time_to_next_launch))
            self.scheduler.add_job(self.run, 'date',
                                   run_date=datetime.datetime.now() + datetime.timedelta(
                                       seconds=self.time_to_next_launch))
        else:
            log(TAG, 'Sleeping for %d seconds.' % DAEMON_SLEEP)
            self.scheduler.add_job(self.run, 'date', run_date=datetime.datetime.now()
                                                              + datetime.timedelta(seconds=DAEMON_SLEEP))