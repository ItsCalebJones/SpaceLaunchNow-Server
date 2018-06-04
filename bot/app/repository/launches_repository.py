import logging

from django.core import serializers
from django.utils.datetime_safe import datetime

from bot.libraries.launchlibrarysdk import LaunchLibrarySDK
from bot.models import Notification, DailyDigestRecord
from bot.utils.deserializer import launch_json_to_model

# import the logging library

# Get an instance of a logger
logger = logging.getLogger('bot.digest')


class LaunchRepository:

    def __init__(self, version=None):

        if version is None:
            version = '1.3'
        self.launchLibrary = LaunchLibrarySDK(version=version)

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
