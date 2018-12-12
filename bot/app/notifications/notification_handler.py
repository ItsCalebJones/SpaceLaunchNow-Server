import logging
from datetime import datetime

import pytz
from pyfcm import FCMNotification

from bot.utils.config import keys
from bot.utils.util import get_fcm_topics_and_onesignal_segments
from spacelaunchnow import config

logger = logging.getLogger('notifications')


class NotificationHandler:
    def __init__(self, debug=None):
        if debug is None:
            self.DEBUG = config.DEBUG
        else:
            self.DEBUG = debug

    def send_notification(self, launch, notification_type, notification):
        current_time = datetime.now(tz=pytz.utc)
        launch_time = launch.net
        diff = int((launch_time - current_time).total_seconds())
        logger.info('Creating %s notification for %s' % (notification_type, launch.name))

        if notification_type == 'netstampChanged':
            if launch.status.id == 1:
                contents = 'UPDATE: New launch attempt scheduled on %s at %s.' % (launch.net.strftime("%A, %B %d"),
                                                                                  launch.net.strftime("%H:%M UTC"))
            elif launch.status.id == 2 or launch.status == 5:
                contents = 'UPDATE: Launch has slipped, new launch date is unconfirmed.'
            else:
                logger.error("Invalid state for sending a notification - Launch: %s" % launch)
                return
        elif notification_type == 'tenMinutes':
            minutes = round(diff / 60)
            if minutes is 0:
                minutes = "less then one"
            if launch.status.id == 1:
                contents = 'Launch attempt from %s in %s minute(s).' % (launch.pad.location.name, minutes)
            else:
                logger.error("Invalid state for sending a notification - Launch: %s" % launch)
                return
        elif notification_type == 'oneMinute':
            if launch.status.id == 1:
                contents = 'Launch attempt from %s in less then one minute.' % launch.pad.location.name
            else:
                logger.error("Invalid state for sending a notification - Launch: %s" % launch)
                return
        elif notification_type == 'twentyFourHour':
            hours = round(diff / 60 / 60)
            if hours is 23:
                hours = 24
            if launch.status.id == 1:
                contents = 'Launch attempt from %s in %s hours.' % (launch.pad.location.name, hours)
            elif launch.status.id == 2 or launch.status.id == 5:
                contents = 'Launch might be launching from %s in %s hours.' % (launch.pad.location.name, hours)
            else:
                logger.error("Invalid state for sending a notification - Launch: %s" % launch)
                return
        elif notification_type == 'oneHour':
            if launch.status.id == 1:
                contents = 'Launch attempt from %s in one hour.' % launch.pad.location.name
            elif launch.status.id == 2 or launch.status.id == 5:
                contents = 'Launch might be launching from %s in one hour.' % launch.pad.location.name
            else:
                logger.error("Invalid state for sending a notification - Launch: %s" % launch)
                return
        elif notification_type == 'success':
            if launch.mission is not None\
                    and launch.mission.orbit is not None\
                    and launch.mission.orbit.name is not None:
                contents = 'Successful launch to %s by %s' % (launch.mission.orbit.name,
                                                              launch.rocket.configuration.launch_agency.name)
            else:
                contents = 'Successful launch by %s' % launch.rocket.configuration.launch_agency.name

        elif notification_type == 'failure':
            contents = 'A launch failure has occurred.'

        elif notification_type == 'partial_failure':
            contents = 'A partial launch failure has occurred.'

        elif notification_type == 'inFlight':

            if launch.mission is not None\
                    and launch.mission.orbit is not None\
                    and launch.mission.orbit.name is not None:
                contents = '%s is in flight to %s!' % (launch.rocket.configuration.name, launch.mission.orbit.name)
            else:
                contents = '%s is in flight!' % launch.rocket.configuration.name

        else:
            launch_time = launch.net
            contents = 'Launch attempt from %s on %s at %s.' % (launch.pad.location.name,
                                                                launch_time.strftime("%A, %B %d"),
                                                                launch_time.strftime("%H:%M UTC"))

        # Create a notification
        topics_and_segments = get_fcm_topics_and_onesignal_segments(launch,
                                                                    notification_type=notification_type,
                                                                    debug=self.DEBUG)
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
                  "launch_id": launch.launch_library_id,
                  "launch_name": launch.name,
                  "launch_image": image,
                  "launch_net": launch.net.strftime("%B %d, %Y %H:%M:%S %Z"),
                  "launch_location": launch.pad.location.name,
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
