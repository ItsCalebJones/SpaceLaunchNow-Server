import re
from django.core import serializers

from django.utils.datetime_safe import datetime
import datetime as dtime
import pytz
from twitter import Twitter, OAuth, TwitterHTTPError
from bot.app.instagram import InstagramBot
from bot.app.repository.launches_repository import LaunchRepository
from bot.utils.config import keys
from bot.models import Notification
from bot.utils.util import seconds_to_time, get_fcm_topics_and_onesignal_segments
from pyfcm import FCMNotification
import logging

from spacelaunchnow import config

AUTH_TOKEN_HERE = keys['AUTH_TOKEN_HERE']
APP_ID = keys['APP_ID']
DAEMON_SLEEP = 600
TAG = 'Notification Server'

# Get an instance of a logger
logger = logging.getLogger('bot.notifications')


def json_default(value):
    if isinstance(value, dtime.date):
        return dict(year=value.year, month=value.month, day=value.day)
    else:
        return value.__dict__


def get_message(launch, diff):
    return '%s launching from %s by %s in %s. \n %s' % (launch.name, launch.location.name,
                                                        launch.rocket.configuration.launch_agency.name,
                                                        seconds_to_time(diff),
                                                        'https://spacelaunchnow.me/launch/%s' % launch.slug)


class LaunchLibrarySync:
    def __init__(self, debug=None, version=None):
        if version is None:
            version = '1.4.1'
        self.repository = LaunchRepository(version=version)
        if debug is None:
            self.DEBUG = config.DEBUG
        else:
            self.DEBUG = debug
        self.twitter = Twitter(
            auth=OAuth(keys['TOKEN_KEY'], keys['TOKEN_SECRET'], keys['CONSUMER_KEY'], keys['CONSUMER_SECRET'])
        )
        self.instagram = InstagramBot()

    def check_next_launch(self):
        for launch in self.repository.get_next_launches(next_count=10):
            if launch.net:
                current_time = datetime.now(tz=pytz.utc)
                launch_time = launch.net
                if current_time <= launch_time:
                    diff = int((launch_time - current_time).total_seconds())
                    logger.debug('%s in %s hours' % (launch.name, (diff / 60) / 60))
                    self.check_next_stamp_changed(diff, launch)

    def netstamp_changed(self, launch, notification, diff):
        logger.info('Netstamp change detected for %s - now launching in %d seconds.' % (launch.name, diff))
        date = launch.net
        message = 'SCHEDULE UPDATE: %s now launching in %s at %s.' % (launch.name,
                                                                      seconds_to_time(diff),
                                                                      date.strftime("%H:%M %Z (%d/%m)"))

        old_diff = notification.last_net_stamp - datetime.now(tz=pytz.utc)
        if old_diff.total_seconds() < 172800:
            logger.info('Netstamp Changed and within window - sending mobile notification.')
            self.send_notification(launch, 'netstampChanged', notification)
        self.send_to_twitter(message, notification)

        notification.last_net_stamp = notification.launch.net
        notification.last_net_stamp_timestamp = datetime.now(tz=pytz.utc)
        launch.save()

        # If launch is within 24 hours...
        if 86400 >= diff > 3600:
            logger.info('Launch is within 24 hours, resetting notifications.')
            notification.wasNotifiedTwentyFourHour = True
            notification.wasNotifiedOneHour = False
            notification.wasNotifiedTenMinutes = False

            notification.wasNotifiedTwentyFourHourTwitter = True
            notification.wasNotifiedOneHourTwitter = False
            notification.wasNotifiedTenMinutesTwitter = False

            notification.wasNotifiedTwentyFourHourDiscord = True
            notification.wasNotifiedOneHourDiscord = False
            notification.wasNotifiedTenMinutesDiscord = False
        elif 3600 >= diff > 600:
            logger.info('Launch is within one hour, resetting Ten minute notifications.')
            notification.wasNotifiedOneHour = True
            notification.wasNotifiedTwentyFourHour = True

            notification.wasNotifiedOneHourTwitter = True
            notification.wasNotifiedTwentyFourHourTwitter = True

            notification.wasNotifiedOneHourDiscord = True
            notification.wasNotifiedTwentyFourHourDiscord = True
        elif diff <= 600:
            logger.info('Launch is within ten minutes.')
            notification.wasNotifiedOneHour = True
            notification.wasNotifiedTwentyFourHour = True
            notification.wasNotifiedTenMinutes = True

            notification.wasNotifiedOneHourTwitter = True
            notification.wasNotifiedTwentyFourHourTwitter = True
            notification.wasNotifiedTenMinutesTwitter = True

            notification.wasNotifiedOneHourDiscord = True
            notification.wasNotifiedTwentyFourHourDiscord = True
            notification.wasNotifiedTenMinutesDiscord = True
        elif diff >= 86400:
            notification.wasNotifiedTwentyFourHour = False
            notification.wasNotifiedOneHour = False
            notification.wasNotifiedTenMinutes = False

            notification.wasNotifiedTwentyFourHourTwitter = False
            notification.wasNotifiedOneHourTwitter = False
            notification.wasNotifiedTenMinutesTwitter = False

            notification.wasNotifiedTwentyFourHourDiscord = False
            notification.wasNotifiedOneHourDiscord = False
            notification.wasNotifiedTenMinutesDiscord = False
        notification.save()

    def check_twitter(self, diff, launch, notification):
        logger.debug('Diff - %d for %s' % (diff, launch.name,))
        logger.debug('LAUNCH DATA: %s', serializers.serialize('json', [launch, ]))
        logger.debug('NOTIFICATION DATA: %s', serializers.serialize('json', [notification, ]))
        if notification.last_twitter_post is not None:
            time_since_twitter = (datetime.now(tz=pytz.utc) - notification.last_twitter_post).total_seconds()
            logger.debug('Seconds since last update on Twitter %d for %s' % (time_since_twitter,
                                                                            launch.name))
            if diff <= 86400 and notification.wasNotifiedTwentyFourHourTwitter is False:
                message = get_message(launch, diff)
                logger.info(message)
                notification.wasNotifiedTwentyFourHourTwitter = True
                notification.save()
                self.send_to_twitter(message, notification)
            elif 3600 >= diff > 600 and time_since_twitter >= 43200 and notification.wasNotifiedOneHourTwitter is False:
                message = get_message(launch, diff)
                logger.info(message)
                notification.wasNotifiedOneHourTwitter = True
                notification.save()
                self.send_to_twitter(message, notification)
            elif 600 >= diff > 0 and (time_since_twitter >= 600) and notification.wasNotifiedTenMinutesTwitter is False:
                message = get_message(launch, diff)
                logger.info(message)
                notification.wasNotifiedTenMinutesTwitter = True
                notification.save()
                self.send_to_twitter(message, notification)
        elif notification.last_twitter_post is None:
            if diff <= 86400:
                message = get_message(launch, diff)
                logger.info(message)
                self.send_to_twitter(message, notification)
                notification.wasNotifiedTwentyFourHourTwitter = True
                notification.save()
            elif 3600 >= diff > 600:
                message = get_message(launch, diff)
                logger.info(message)
                notification.wasNotifiedOneHourTwitter = True
                notification.save()
                self.send_to_twitter(message, notification)
            elif 600 >= diff > 0:
                message = get_message(launch, diff)
                logger.info(message)
                notification.wasNotifiedTenMinutesTwitter = True
                notification.save()
                self.send_to_twitter(message, notification)

    def check_next_stamp_changed(self, diff, launch):
        notification = Notification.objects.get(launch=launch)
        if notification.last_net_stamp is not None:
            if (notification.last_net_stamp - launch.net).total_seconds() > 600:
                self.netstamp_changed(launch, notification, diff)
            else:
                self.check_launch_window(diff, launch, notification)
        else:
            self.check_launch_window(diff, launch, notification)

    def check_launch_window(self, diff, launch, notification):
        self.check_twitter(diff, launch, notification)
        logger.debug('Checking launch window for %s' % notification.launch.name)

        # If launch is within 24 hours...
        if 86400 >= diff > 3600 and not notification.wasNotifiedTwentyFourHour:
            logger.info('%s is within 24 hours, sending notifications.' % launch.name)
            self.send_notification(launch, 'twentyFourHour', notification, diff)
            notification.wasNotifiedTwentyFourHour = True
        elif 3600 >= diff > 600 and not notification.wasNotifiedOneHour:
            logger.info('%s is within one hour, sending notifications.' % launch.name)
            self.send_notification(launch, 'oneHour', notification, diff)
            notification.wasNotifiedOneHour = True
        elif diff <= 600 and not notification.wasNotifiedTenMinutes:
            logger.info('%s is within ten minutes, sending notifications.' % launch.name)
            self.send_notification(launch, 'tenMinutes', notification, diff)
            notification.wasNotifiedTenMinutes = True
        else:
            logger.info('%s does not meet notification criteria.' % notification.launch.name)
        notification.save()

    def send_to_twitter(self, message, notification):
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

            notification.last_twitter_post = datetime.now(tz=pytz.utc)
            notification.last_net_stamp = notification.launch.net
            notification.last_net_stamp_timestamp = datetime.now(tz=pytz.utc)
            logger.info('Updating Notification %s to timestamp %s' % (notification.launch.id,
                                                                      notification.last_twitter_post
                                                                      .strftime("%A %d. %B %Y")))

            notification.save()
        except TwitterHTTPError as e:
            logger.error("%s %s" % (str(e), message))

    def send_notification(self, launch, notification_type, notification, diff=None):
        logger.info('Creating notification for %s' % launch.name)

        if notification_type == 'netstampChanged':
            contents = 'UPDATE: New launch attempt scheduled on %s at %s.' % (launch.net.strftime("%A, %B %d"),
                                                                              launch.net.strftime("%H:%M UTC"))
        elif notification_type == 'tenMinutes':
            minutes = diff / 60
            if minutes is 0:
                minutes = "less then one"
            contents = 'Launch attempt from %s in %s minute(s).' % (launch.location.name, minutes)
        elif notification_type == 'twentyFourHour':
            hours = diff / 60 / 60
            if hours is 23:
                hours = 24
            contents = 'Launch attempt from %s in %s hours.' % (launch.location.name, hours)
        elif notification_type == 'oneHour':
            contents = 'Launch attempt from %s in one hour.' % launch.location.name

        else:
            launch_time = launch.net
            contents = 'Launch attempt from %s on %s at %s.' % (launch.location.name,
                                                                launch_time.strftime("%A, %B %d"),
                                                                launch_time.strftime("%H:%M UTC"))


        # Create a notification
        topics_and_segments = get_fcm_topics_and_onesignal_segments(launch, debug=self.DEBUG)
        include_segments = topics_and_segments['segments']
        exclude_segments = ['firebase']
        if self.DEBUG:
            exclude_segments.append('Production')
        if len(launch.vid_urls.all()) > 0:
            webcast = True
        else:
            webcast = False
        image = ''
        if launch.rocket.configuration.launch_agency.image_url:
            image = launch.rocket.configuration.launch_agency.image_url.url
        elif launch.rocket.configuration.launch_agency.legacy_image_url:
            image = launch.rocket.configuration.launch_agency.legacy_image_url
        kwargs = dict(
            content_available=True,
            excluded_segments=exclude_segments,
            included_segments=include_segments,
            isAndroid=True,
            data={"silent": True,
                  "background": True,
                  "launch_id": launch.id,
                  "launch_name": launch.name,
                  "launch_image": image,
                  "launch_net": launch.net.strftime("%B %d, %Y %H:%M:%S %Z"),
                  "launch_location": launch.location.name,
                  "notification_type": notification_type,
                  "webcast": webcast
                  }
        )
        # url = 'https://spacelaunchnow.me/launch/%d/' % launch.id
        heading = 'Space Launch Now'
        time_since_last_notification = None
        if notification.last_notification_sent is not None:
            time_since_last_notification = datetime.now(tz=pytz.utc) - notification.last_notification_sent
        if time_since_last_notification is not None and time_since_last_notification.total_seconds() < 600 and not self.DEBUG:
            logger.info('Cannot send notification - too soon since last notification!')
        else:
            logger.info('----------------------------------------------------------')
            logger.info('Sending notification - %s' % contents)
            logger.info('Notification Data - %s' % kwargs)
            push_service = FCMNotification(api_key=keys['FCM_KEY'])
            android_topics = topics_and_segments['topics']
            flutter_topics = get_fcm_topics_and_onesignal_segments(launch,
                                                                   debug=self.DEBUG,
                                                                   flutter=True,
                                                                   notification_type=notification_type)['topics']
            logger.info("Flutter Topics: %s" % flutter_topics)
            logger.info(topics_and_segments)
            android_result = push_service.notify_topic_subscribers(data_message=kwargs['data'],
                                                                   condition=android_topics,
                                                                   time_to_live=86400, )

            flutter_result = push_service.notify_topic_subscribers(data_message=kwargs['data'],
                                                                   condition=flutter_topics,
                                                                   time_to_live=86400,
                                                                   message_title=launch.name,
                                                                   message_body=contents)
            logger.debug(android_result)
            logger.debug(flutter_result)
            notification.last_notification_sent = datetime.now(tz=pytz.utc)
            notification.save()
            logger.info('----------------------------------------------------------')
