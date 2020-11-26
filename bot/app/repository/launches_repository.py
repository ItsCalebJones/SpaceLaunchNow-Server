import logging

from django.core import serializers
from django.utils.datetime_safe import datetime
from pytz import utc

from bot.libraries.launchlibrarysdk import LaunchLibrarySDK
from bot.models import LaunchNotificationRecord, DailyDigestRecord
from bot.utils.deserializer import launch_json_to_model, launch_status_json_to_model, mission_type_json_to_model, \
    agency_type_json_to_model, rocket_json_to_model

# import the logging library

# Get an instance of a logger
logger = logging.getLogger('bot.digest')


class LaunchRepository:

    def __init__(self, version=None):

        if version is None:
            version = '1.4.1'
        self.launchLibrary = LaunchLibrarySDK(version=version)

    def get_next_launches(self, next_count=5, all=False, status=None):
        logger.info("Daily Digest running...")
        launches = []
        count = 0
        total = None
        while total is None or count < total:
            response = self.launchLibrary.get_next_launches(next_count=next_count, offset=count, status=status)
            if response.status_code is 200:
                response_json = response.json()
                count = response_json['count'] + response_json['offset']
                total = response_json['total']
                launch_data = response_json['launches']
                logger.info("Saving next %i launches - %s out of %s" % (len(launch_data), count, total))

                for launch in launch_data:
                    launch = launch_json_to_model(launch)
                    logger.debug(u"Saving Launch: %s" % launch.name)
                    launch.save()
                    launches.append(launch)
                if not all:
                    break
            else:
                logger.error('ERROR ' + str(response.status_code))
                logger.error('RESPONSE: ' + response.text)
                logger.error('URL: ' + response.url)
                break
        return launches

    def get_next_launch(self):
        response = self.launchLibrary.get_next_launches()
        if response.status_code is 200:
            response_json = response.json()
            launch_data = response_json['launches']
            logger.debug("Found %i launches" % len(launch_data))
            logger.debug("DATA: %s" % launch_data)
            for launch in launch_data:
                return launch_json_to_model(launch)
        else:
            logger.error(response.status_code + ' ' + response)

    def get_next_weeks_launches(self):
        logger.info("Weekly Digest running...")
        launches = []
        count = 0
        total = None
        while total is None or count < total:
            response = self.launchLibrary.get_next_weeks_launches(offset=count)
            if response.status_code is 200:
                response_json = response.json()
                count = response_json['count'] + response_json['offset']
                total = response_json['total']
                launch_data = response_json['launches']
                logger.info("Saving next %i launches - %s out of %s" % (len(launch_data), count, total))

                for launch in launch_data:
                    launch = launch_json_to_model(launch)
                    launch.save()
                    launches.append(launch)
            else:
                logger.error('ERROR ' + str(response.status_code))
                logger.error('RESPONSE: ' + response.text)
                logger.error('URL: ' + response.url)
                break
        return launches

    def get_previous_launches(self):
        logger.info("Getting previous launches")
        launches = []
        count = 0
        total = None
        while total is None or count < total:
            response = self.launchLibrary.get_previous_launches(offset=count)
            try:
                if response.status_code is 200:
                    response_json = response.json()
                    count = response_json['count'] + response_json['offset']
                    total = response_json['total']
                    launch_data = response_json['launches']
                    logger.info("Saving next %i launches - %s out of %s" % (len(launch_data), count, total))

                    for launch in launch_data:
                        launch = launch_json_to_model(launch)
                        launch.save()
                        launches.append(launch)
                        logger.debug("Saving %d" % launch.id)
                else:
                    logger.error('ERROR ' + str(response.status_code))
                    logger.error('RESPONSE: ' + response.text)
                    logger.error('URL: ' + response.url)
                    break
            except Exception as e:
                logger.error(e)
                logger.error('RESPONSE: ' + response.text)
                logger.error('URL: ' + response.url)
                break
        return launches

    def get_recent_previous_launches(self):
        logger.info("Getting recent previous launches")
        launches = []
        count = 0
        total = None
        while total is None or count < total:
            response = self.launchLibrary.get_recent_previous_launches(offset=count)
            if response.status_code is 200:
                response_json = response.json()
                count = response_json['count'] + response_json['offset']
                total = response_json['total']
                launch_data = response_json['launches']
                logger.info("Saving next %i launches - %s out of %s" % (len(launch_data), count, total))

                for launch in launch_data:
                    launch = launch_json_to_model(launch)
                    launch.save()
                    launches.append(launch)
            else:
                logger.error('ERROR ' + str(response.status_code))
                logger.error('RESPONSE: ' + response.text)
                logger.error('URL: ' + response.url)
                break
        return launches

    def is_launch_deleted(self, id):
        response = self.launchLibrary.get_launch_by_id(id)
        if response.status_code == 200:
            logger.debug("Launch is NOT deleted - %s" % id)
            response_json = response.json()
            launch_data = response_json['launches']
            logger.debug("Found %i launches" % len(launch_data))
            for launch in launch_data:
                return launch_json_to_model(launch)
            return False
        elif response.status_code == 404:
            logger.debug("Launch is Stale - %s" % id)
            return True
        else:
            return False

    def get_launch_by_id(self, id):
        response = self.launchLibrary.get_launch_by_id(id)
        if response.status_code == 200:
            response_json = response.json()
            launches_json = response_json['launches']
            for launch_json in launches_json:
                launch = launch_json_to_model(launch_json)
                launch.save()
                return launch

    def get_launch_status(self):
        response = self.launchLibrary.get_launch_status()
        if response.status_code == 200:
            response_json = response.json()
            statuses_json = response_json['types']
            statuses = []
            for status_json in statuses_json:
                status = launch_status_json_to_model(status_json)
                status.save()
                statuses.append(status)
            return statuses

    def get_agency_type(self):
        response = self.launchLibrary.get_agency_type()
        if response.status_code == 200:
            response_json = response.json()
            statuses_json = response_json['types']
            statuses = []
            for status_json in statuses_json:
                status = agency_type_json_to_model(status_json)
                status.save()
                statuses.append(status)
            return statuses

    def get_mission_type(self):
        response = self.launchLibrary.get_mission_type()
        if response.status_code == 200:
            response_json = response.json()
            statuses_json = response_json['types']
            statuses = []
            for status_json in statuses_json:
                status = mission_type_json_to_model(status_json)
                status.save()
                statuses.append(status)
            return statuses

    def get_launcher_configs(self):
        response = self.launchLibrary.get_rockets()
        if response.status_code == 200:
            response_json = response.json()
            rockets_json = response_json['rockets']
            for rocket in rockets_json:
                rocket_json_to_model(rocket)


def update_notification_record(launch):
    notification = LaunchNotificationRecord.objects.get(launch_id=launch.id)
    notification.last_net_stamp = launch.net
    notification.last_net_stamp_timestamp = datetime.now(tz=utc)
    logger.info('Updating Notification %s to timestamp %s' % (launch.name,
                                                              launch.net.strftime("%A %d %B %Y")))
    notification.save()


def create_daily_digest_record(total, messages, launches):
    data = []

    for launch in launches:
        launch_json = serializers.serialize('json', [launch, ])
        data.append(launch_json)
    DailyDigestRecord.objects.create(timestamp=datetime.now(tz=utc),
                                     messages=messages,
                                     count=total,
                                     data=data)
