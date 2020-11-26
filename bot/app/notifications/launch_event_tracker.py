import datetime as dtime

from django.db.models import Q
from django.utils.datetime_safe import datetime

import logging

import pytz

from api.models import Launch
from bot.app.notifications.netstamp_handler import NetstampHandler
from bot.app.notifications.notification_handler import NotificationHandler
from bot.app.notifications.social_handler import SocialEvents
from bot.models import LaunchNotificationRecord, Notification
from bot.utils.util import seconds_to_time
from spacelaunchnow import config

logger = logging.getLogger('bot.notifications')


class LaunchEventTracker:
    def __init__(self, debug=None):
        if debug is None:
            self.DEBUG = config.DEBUG
        else:
            self.DEBUG = debug
        self.social = SocialEvents()
        self.notification_handler = NotificationHandler()
        self.netstamp = NetstampHandler()

    def check_next_stamp_changed(self, launch):
        logger.debug('Running check_next_stamp_changed for %s...', launch.name)
        notification, created = LaunchNotificationRecord.objects.get_or_create(launch_id=launch.id)
        if launch.net:
            current_time = datetime.now(tz=pytz.utc)
            launch_time = launch.net
            logger.debug('Times launch %s - %s', current_time, launch_time)
            if current_time <= launch_time:
                diff = int((launch_time - current_time).total_seconds())
                logger.debug('Time to launch %s', seconds_to_time(diff))
                if notification.last_net_stamp is not None:
                    if abs((notification.last_net_stamp - launch.net)).total_seconds() > 7200:
                        logger.info('Netstamp changed from %s to %s' % (notification.last_net_stamp, launch.net))
                        self.netstamp.netstamp_changed(launch, notification, diff)

    def check_success(self, time_threshold_past_two_days, time_threshold_24_hour):
        logger.debug('Running check_success...')
        launches = Launch.objects.filter(Q(status__id=3) | Q(status__id=4) | Q(status__id=7),
                                         net__lte=time_threshold_24_hour,
                                         net__gte=time_threshold_past_two_days,
                                         notifications_enabled=True)

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
            notification, created = LaunchNotificationRecord.objects.get_or_create(launch_id=launch.id)
            logger.debug('Notification for %s: %s', launch.name, notification.__dict__)
            try:
                if not notification.wasNotifiedSuccess:
                    logger.info('Sending mobile notification for %s!', launch.name)
                    notification.wasNotifiedSuccess = True
                    notification.save()
                    self.notification_handler.send_notification(launch=launch,
                                                                notification_type=status,
                                                                notification=notification)
            except Exception as e:
                logger.error(e)

            try:
                if not notification.wasNotifiedSuccessTwitter:
                    logger.info('Sending Twitter notification for %s!', launch.name)
                    notification.wasNotifiedSuccessTwitter = True
                    notification.last_twitter_post = datetime.now(tz=pytz.utc)
                    notification.last_net_stamp = launch.net
                    notification.last_net_stamp_timestamp = datetime.now(tz=pytz.utc)
                    logger.debug('Updating Notification %s to timestamp %s' % (launch.id,
                                                                               notification.last_twitter_post
                                                                               .strftime("%A %d. %B %Y")))
                    notification.save()
                    self.social.send_to_twitter(launch=launch,
                                                notification_type=status)
            except Exception as e:
                logger.error(e)

    def check_in_flight(self):
        logger.debug('Running check_in_flight...')
        launches = Launch.objects.filter(status__id=6, notifications_enabled=True)

        logger.debug('Found %d launches in flight - checking state.', len(launches))
        for launch in launches:
            notification, created = LaunchNotificationRecord.objects.get_or_create(launch_id=launch.id)
            logger.debug('Notification for %s: %s', launch.name, notification.__dict__)
            try:
                if not notification.wasNotifiedInFlight:
                    logger.info('Sending mobile notification for %s!', launch.name)
                    notification.wasNotifiedInFlight = True
                    notification.save()
                    self.notification_handler.send_notification(launch=launch,
                                                                notification_type='inFlight',
                                                                notification=notification)
            except Exception as e:
                logger.error(e)

            try:
                if not notification.wasNotifiedInFlightTwitter:
                    logger.info('Sending Twitter notification for %s!', launch.name)
                    notification.wasNotifiedInFlightTwitter = True
                    notification.last_twitter_post = datetime.now(tz=pytz.utc)
                    notification.last_net_stamp = launch.net
                    notification.last_net_stamp_timestamp = datetime.now(tz=pytz.utc)
                    logger.debug('Updating Notification %s to timestamp %s' % (launch.id,
                                                                               notification.last_twitter_post
                                                                               .strftime("%A %d. %B %Y")))
                    notification.save()
                    self.social.send_to_twitter(launch=launch,
                                                notification_type='inFlight')
            except Exception as e:
                logger.error(e)

    def check_custom(self):
        logger.debug('Running check_in_flight...')
        pending_ios = Notification.objects.filter(Q(send_ios=True) & Q(send_ios_complete=False))
        pending_android = Notification.objects.filter(Q(send_android=True) & Q(send_android_complete=False))
        for pending in pending_ios:
            pending.send_ios_complete = True
            pending.save()
            self.notification_handler.send_custom_ios(pending)
        for pending in pending_android:
            pending.send_android_complete = True
            pending.save()
            self.notification_handler.send_custom_android(pending)

    def check_one_minute(self, time_threshold_1_minute):
        logger.debug('Running check_one_minute...')
        launches = Launch.objects.filter(net__lte=time_threshold_1_minute,
                                         net__gte=dtime.datetime.now(tz=pytz.utc),
                                         notifications_enabled=True)

        logger.debug('Found %d launches within one minute - checking state.', len(launches))
        for launch in launches:
            self.check_next_stamp_changed(launch)
            notification, created = LaunchNotificationRecord.objects.get_or_create(launch_id=launch.id)
            logger.debug('Notification for %s: %s', launch.name, notification.__dict__)

            try:
                if not notification.wasNotifiedOneMinute:
                    logger.info('Sending mobile notification for %s!', launch.name)
                    notification.wasNotifiedOneMinute = True
                    notification.save()
                    self.notification_handler.send_notification(launch=launch,
                                                                notification_type='oneMinute',
                                                                notification=notification)
            except Exception as e:
                logger.error(e)

            try:
                if not notification.wasNotifiedOneMinuteTwitter:
                    logger.info('Sending Twitter notification for %s!', launch.name)
                    notification.wasNotifiedOneMinuteTwitter = True
                    notification.last_twitter_post = datetime.now(tz=pytz.utc)
                    notification.last_net_stamp = launch.net
                    notification.last_net_stamp_timestamp = datetime.now(tz=pytz.utc)
                    logger.debug('Updating Notification %s to timestamp %s' % (launch.id,
                                                                               notification.last_twitter_post
                                                                               .strftime("%A %d. %B %Y")))
                    notification.save()
                    self.social.send_to_twitter(launch=launch,
                                                notification_type='oneMinute')
            except Exception as e:
                logger.error(e)

    def check_ten_minute(self, time_threshold_10_minute, time_threshold_1_minute):
        logger.debug('Running check_ten_minute...')
        launches = Launch.objects.filter(net__lte=time_threshold_10_minute,
                                         net__gte=time_threshold_1_minute,
                                         notifications_enabled=True)

        logger.debug('Found %d launches within ten minutes - checking state.', len(launches))
        for launch in launches:
            self.check_next_stamp_changed(launch)
            notification, created = LaunchNotificationRecord.objects.get_or_create(launch_id=launch.id)
            logger.debug('Notification for %s: %s', launch.name, notification.__dict__)

            try:
                if not notification.wasNotifiedTenMinutes:
                    logger.info('Sending mobile notification for %s!', launch.name)
                    notification.wasNotifiedTenMinutes = True
                    notification.save()
                    self.notification_handler.send_notification(launch=launch,
                                                                notification_type='tenMinutes',
                                                                notification=notification)
            except Exception as e:
                logger.error(e)

            try:
                if not notification.wasNotifiedTenMinutesTwitter:
                    logger.info('Sending Twitter notification for %s!', launch.name)
                    notification.wasNotifiedTenMinutesTwitter = True
                    notification.last_twitter_post = datetime.now(tz=pytz.utc)
                    notification.last_net_stamp = launch.net
                    notification.last_net_stamp_timestamp = datetime.now(tz=pytz.utc)
                    logger.debug('Updating Notification %s to timestamp %s' % (launch.id,
                                                                               notification.last_twitter_post
                                                                               .strftime("%A %d. %B %Y")))

                    notification.save()
                    self.social.send_to_twitter(launch=launch,
                                                notification_type='tenMinutes')
            except Exception as e:
                logger.error(e)

    def check_twenty_four_hour(self, time_threshold_1_hour, time_threshold_24_hour):
        logger.debug('Running check_twenty_four_hour...')
        launches = Launch.objects.filter(net__lte=time_threshold_24_hour,
                                         net__gte=time_threshold_1_hour,
                                         notifications_enabled=True)

        logger.debug('Found %d launches within twenty four hours - checking state.', len(launches))

        for launch in launches:
            self.check_next_stamp_changed(launch)
            notification, created = LaunchNotificationRecord.objects.get_or_create(launch_id=launch.id)
            logger.debug('Notification for %s: %s', launch.name, notification.__dict__)

            try:
                if not notification.wasNotifiedTwentyFourHour:
                    logger.info('Sending mobile notification for %s!', launch.name)
                    notification.wasNotifiedTwentyFourHour = True
                    notification.save()
                    self.notification_handler.send_notification(launch=launch,
                                                                notification_type='twentyFourHour',
                                                                notification=notification)
            except Exception as e:
                logger.error(e)

            try:
                if not notification.wasNotifiedTwentyFourHourTwitter:
                    logger.info('Sending Twitter notification for %s!', launch.name)
                    notification.wasNotifiedTwentyFourHourTwitter = True
                    notification.last_twitter_post = datetime.now(tz=pytz.utc)
                    notification.last_net_stamp = launch.net
                    notification.last_net_stamp_timestamp = datetime.now(tz=pytz.utc)
                    logger.debug('Updating Notification %s to timestamp %s' % (launch.id,
                                                                               notification.last_twitter_post
                                                                               .strftime("%A %d. %B %Y")))
                    notification.save()
                    self.social.send_to_all(launch=launch,
                                            notification_type='twentyFourHour')
            except Exception as e:
                logger.error(e)

    def check_one_hour(self, time_threshold_10_minute, time_threshold_1_hour):
        logger.debug('Running check_one_hour...')
        launches = Launch.objects.filter(net__lte=time_threshold_1_hour,
                                         net__gte=time_threshold_10_minute,
                                         notifications_enabled=True)

        logger.debug('Found %d launches within an hour - checking state.', len(launches))

        for launch in launches:
            self.check_next_stamp_changed(launch)
            notification, created = LaunchNotificationRecord.objects.get_or_create(launch_id=launch.id)
            logger.debug('Notification for %s: %s', launch.name, notification.__dict__)

            try:
                if not notification.wasNotifiedOneHour:
                    logger.info('Sending mobile notification for %s!', launch.name)
                    notification.wasNotifiedOneHour = True
                    notification.save()
                    self.notification_handler.send_notification(launch=launch,
                                                                notification_type='oneHour',
                                                                notification=notification)
            except Exception as e:
                logger.error(e)

            try:
                if not notification.wasNotifiedOneHourTwitter:
                    logger.info('Sending Twitter notification for %s!', launch.name)
                    notification.wasNotifiedOneHourTwitter = True
                    notification.last_twitter_post = datetime.now(tz=pytz.utc)
                    notification.last_net_stamp = launch.net
                    notification.last_net_stamp_timestamp = datetime.now(tz=pytz.utc)
                    logger.debug('Updating Notification %s to timestamp %s' % (launch.id,
                                                                               notification.last_twitter_post
                                                                               .strftime("%A %d. %B %Y")))
                    notification.save()
                    self.social.send_to_twitter(launch=launch,
                                                notification_type='oneHour')
                    if launch.infographic_url:
                        self.social.buffer.send_to_all(
                            message="%s in one hour!\n\nInfographic Credit: @geoffdbarrett" % launch.name,
                            image=launch.infographic_url.url, now=True)
            except Exception as e:
                logger.error(e)

    def check_webcast_live(self, time_threshold_1_hour, time_threshold_10_minute):
        logger.info('Running check webcast...')
        launches = Launch.objects.filter(net__gte=time_threshold_10_minute,
                                         net__lte=time_threshold_1_hour,
                                         webcast_live=True,
                                         notifications_enabled=True)
        logger.info('Found %d launches within an hour - checking state.', len(launches))

        for launch in launches:
            self.check_next_stamp_changed(launch)
            notification, created = LaunchNotificationRecord.objects.get_or_create(launch_id=launch.id)
            logger.info('Notification for %s: %s', launch.name, notification.__dict__)

            try:
                if not notification.wasNotifiedWebcastLive:
                    logger.info('Sending mobile notification for %s!', launch.name)
                    notification.wasNotifiedWebcastLive = True
                    notification.save()
                    self.notification_handler.send_notification(launch=launch,
                                                                notification_type='webcastLive',
                                                                notification=notification)
            except Exception as e:
                logger.error(e)

            try:
                if not notification.wasNotifiedWebcastLiveTwitter:
                    logger.info('Sending Twitter notification for %s!', launch.name)
                    notification.wasNotifiedWebcastLiveTwitter = True
                    notification.last_twitter_post = datetime.now(tz=pytz.utc)
                    notification.last_net_stamp = launch.net
                    notification.last_net_stamp_timestamp = datetime.now(tz=pytz.utc)
                    logger.info('Updating Notification %s to timestamp %s' % (launch.id,
                                                                               notification.last_twitter_post
                                                                               .strftime("%A %d. %B %Y")))
                    notification.save()
                    self.social.send_to_twitter(launch=launch,
                                                notification_type='webcastLive')
            except Exception as e:
                logger.error(e)

    def check_this_week(self, time_threshold_1_week, time_threshold_24_hour):
        logger.debug('Running check_this_week...')
        launches = Launch.objects.filter(net__lte=time_threshold_1_week,
                                         net__gte=time_threshold_24_hour,
                                         notifications_enabled=True)

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

        self.check_webcast_live(time_threshold_1_hour, time_threshold_10_minute)

        self.check_ten_minute(time_threshold_10_minute, time_threshold_1_minute)

        self.check_one_minute(time_threshold_1_minute)

        self.check_in_flight()

        self.check_success(time_threshold_past_two_days, time_threshold_24_hour)

        self.check_custom()
