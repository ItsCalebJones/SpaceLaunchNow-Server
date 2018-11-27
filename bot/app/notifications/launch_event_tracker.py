import datetime as dtime

from django.db.models import Q
from django.utils.datetime_safe import datetime

import logging

import pytz

from api.models import Launch
from bot.app.notifications.netstamp_handler import NetstampHandler
from bot.app.notifications.notification_handler import NotificationHandler
from bot.app.notifications.twitter_handler import TwitterEvents
from bot.models import Notification
from bot.utils.util import seconds_to_time
from spacelaunchnow import config

logger = logging.getLogger('notifications')


class LaunchEventTracker:
    def __init__(self, debug=None):
        if debug is None:
            self.DEBUG = config.DEBUG
        else:
            self.DEBUG = debug
        self.twitter = TwitterEvents()
        self.notification_handler = NotificationHandler()
        self.netstamp = NetstampHandler()

    def check_next_stamp_changed(self, launch):
        logger.debug('Running check_next_stamp_changed for %s...', launch.name)
        notification = Notification.objects.get(launch=launch)
        if launch.net:
            current_time = datetime.now(tz=pytz.utc)
            launch_time = launch.net
            logger.debug('Times launch %s - %s', current_time, launch_time)
            if current_time <= launch_time:
                diff = int((launch_time - current_time).total_seconds())
                logger.debug('Time to launch %s', seconds_to_time(diff))
                if notification.last_net_stamp is not None:
                    if abs((notification.last_net_stamp - launch.net)).total_seconds() > 3600:
                        logger.info('Netstamp changed!')
                        self.netstamp.netstamp_changed(launch, notification, diff)

    def check_success(self, time_threshold_past_two_days, time_threshold_24_hour):
        logger.debug('Running check_success...')
        launches = Launch.objects.filter(Q(status__id=3) | Q(status__id=4) | Q(status__id=7),
                                         net__lte=time_threshold_24_hour,
                                         net__gte=time_threshold_past_two_days)

        logger.debug('Found %d launches with recent success - checking state.', len(launches))
        for launch in launches:
            if launch.status.id == 3:
                status = 'success'
            elif launch.status.id == 4:
                status = 'failure'
            elif launch.status.id == 7:
                status = 'partial_failure'
            else:
                return
            notification, created = Notification.objects.get_or_create(launch=launch)
            logger.debug('Notification for %s: %s', launch.name, notification.__dict__)
            if not notification.wasNotifiedSuccess:
                logger.info('Sending mobile notification for %s!', launch.name)
                self.notification_handler.send_notification(launch=launch,
                                                            notification_type=status,
                                                            notification=notification)
                notification.wasNotifiedSuccess = True

            if not notification.wasNotifiedSuccessTwitter:
                logger.info('Sending Twitter notification for %s!', launch.name)
                self.twitter.send_to_twitter(launch=launch,
                                             notification_type=status,
                                             notification=notification)
                notification.wasNotifiedSuccessTwitter = True

            notification.save()

    def check_in_flight(self):
        logger.debug('Running check_in_flight...')
        launches = Launch.objects.filter(status__id=6)

        logger.debug('Found %d launches in flight - checking state.', len(launches))

        for launch in launches:
            notification, created = Notification.objects.get_or_create(launch=launch)
            logger.debug('Notification for %s: %s', launch.name, notification.__dict__)
            if not notification.wasNotifiedInFlight:
                logger.info('Sending mobile notification for %s!', launch.name)
                self.notification_handler.send_notification(launch=launch,
                                                            notification_type='inFlight',
                                                            notification=notification)
                notification.wasNotifiedInFlight = True

            if not notification.wasNotifiedInFlightTwitter:
                logger.info('Sending Twitter notification for %s!', launch.name)
                self.twitter.send_to_twitter(launch=launch,
                                             notification_type='inFlight',
                                             notification=notification)
                notification.wasNotifiedInFlightTwitter = True

            notification.save()

    def check_one_minute(self, time_threshold_1_minute):
        logger.debug('Running check_one_minute...')
        launches = Launch.objects.filter(net__lte=time_threshold_1_minute,
                                         net__gte=dtime.datetime.now(tz=pytz.utc))

        logger.debug('Found %d launches within one minute - checking state.', len(launches))

        for launch in launches:
            self.check_next_stamp_changed(launch)
            notification, created = Notification.objects.get_or_create(launch=launch)
            logger.debug('Notification for %s: %s', launch.name, notification.__dict__)
            if not notification.wasNotifiedOneMinute:
                logger.info('Sending mobile notification for %s!', launch.name)
                self.notification_handler.send_notification(launch=launch,
                                                            notification_type='oneMinute',
                                                            notification=notification)
                notification.wasNotifiedOneMinute = True

            if not notification.wasNotifiedOneMinuteTwitter:
                logger.info('Sending Twitter notification for %s!', launch.name)
                self.twitter.send_to_twitter(launch=launch,
                                             notification_type='oneMinute',
                                             notification=notification)
                notification.wasNotifiedOneMinuteTwitter = True

            notification.save()

    def check_ten_minute(self, time_threshold_10_minute, time_threshold_1_minute):
        logger.debug('Running check_ten_minute...')
        launches = Launch.objects.filter(net__lte=time_threshold_10_minute,
                                         net__gte=time_threshold_1_minute)

        logger.debug('Found %d launches within ten minutes - checking state.', len(launches))

        for launch in launches:
            self.check_next_stamp_changed(launch)
            notification, created = Notification.objects.get_or_create(launch=launch)
            logger.debug('Notification for %s: %s', launch.name, notification.__dict__)
            if not notification.wasNotifiedTenMinutes:
                logger.info('Sending mobile notification for %s!', launch.name)
                self.notification_handler.send_notification(launch=launch,
                                                            notification_type='tenMinutes',
                                                            notification=notification)
                notification.wasNotifiedTenMinutes = True

            if not notification.wasNotifiedTenMinutesTwitter:
                logger.info('Sending Twitter notification for %s!', launch.name)
                self.twitter.send_to_twitter(launch=launch,
                                             notification_type='tenMinutes',
                                             notification=notification)
                notification.wasNotifiedTenMinutesTwitter = True

            notification.save()

    def check_twenty_four_hour(self, time_threshold_1_hour, time_threshold_24_hour):
        logger.debug('Running check_twenty_four_hour...')
        launches = Launch.objects.filter(net__lte=time_threshold_24_hour,
                                         net__gte=time_threshold_1_hour)

        logger.debug('Found %d launches within twenty four hours - checking state.', len(launches))

        for launch in launches:
            self.check_next_stamp_changed(launch)
            notification, created = Notification.objects.get_or_create(launch=launch)
            logger.debug('Notification for %s: %s', launch.name, notification.__dict__)
            if not notification.wasNotifiedTwentyFourHour:
                logger.info('Sending mobile notification for %s!', launch.name)
                self.notification_handler.send_notification(launch=launch,
                                                            notification_type='twentyFourHour',
                                                            notification=notification)
                notification.wasNotifiedTwentyFourHour = True

            if not notification.wasNotifiedTwentyFourHourTwitter:
                logger.info('Sending Twitter notification for %s!', launch.name)
                self.twitter.send_to_twitter(launch=launch,
                                             notification_type='twentyFourHour',
                                             notification=notification)
                notification.wasNotifiedTwentyFourHourTwitter = True

            notification.save()

    def check_one_hour(self, time_threshold_10_minute, time_threshold_1_hour):
        logger.debug('Running check_one_hour...')
        launches = Launch.objects.filter(net__lte=time_threshold_1_hour,
                                         net__gte=time_threshold_10_minute)

        logger.debug('Found %d launches within an hour - checking state.', len(launches))

        for launch in launches:
            self.check_next_stamp_changed(launch)
            notification, created = Notification.objects.get_or_create(launch=launch)
            logger.debug('Notification for %s: %s', launch.name, notification.__dict__)
            if not notification.wasNotifiedOneHour:
                logger.info('Sending mobile notification for %s!', launch.name)
                self.notification_handler.send_notification(launch=launch,
                                                            notification_type='oneHour',
                                                            notification=notification)
                notification.wasNotifiedOneHour = True

            if not notification.wasNotifiedOneHourTwitter:
                logger.info('Sending Twitter notification for %s!', launch.name)
                self.twitter.send_to_twitter(launch=launch,
                                             notification_type='oneHour',
                                             notification=notification)
                notification.wasNotifiedOneHourTwitter = True

            notification.save()

    def check_this_week(self, time_threshold_1_week, time_threshold_24_hour):
        logger.debug('Running check_this_week...')
        launches = Launch.objects.filter(net__lte=time_threshold_1_week,
                                         net__gte=time_threshold_24_hour)

        logger.debug('Found %d launches within the week - checking state.', len(launches))

        for launch in launches:
            self.check_next_stamp_changed(launch)

    def check_events(self):
        time_threshold_1_week = dtime.datetime.now(tz=pytz.utc) + dtime.timedelta(days=7)
        time_threshold_24_hour = dtime.datetime.now(tz=pytz.utc) + dtime.timedelta(hours=24)
        time_threshold_1_hour = dtime.datetime.now(tz=pytz.utc) + dtime.timedelta(hours=1)
        time_threshold_10_minute = dtime.datetime.now(tz=pytz.utc) + dtime.timedelta(minutes=10)
        time_threshold_1_minute = dtime.datetime.now(tz=pytz.utc) + dtime.timedelta(minutes=1)
        time_threshold_past_two_days = dtime.datetime.now(tz=pytz.utc) - dtime.timedelta(days=2)

        self.check_this_week(time_threshold_1_week, time_threshold_24_hour)

        self.check_twenty_four_hour(time_threshold_1_hour, time_threshold_24_hour)

        self.check_one_hour(time_threshold_10_minute, time_threshold_1_hour)

        self.check_ten_minute(time_threshold_10_minute, time_threshold_1_minute)

        self.check_one_minute(time_threshold_1_minute)

        self.check_in_flight()

        self.check_success(time_threshold_past_two_days, time_threshold_24_hour)
