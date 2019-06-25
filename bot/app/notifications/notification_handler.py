import logging
from datetime import datetime

import pytz
from pyfcm import FCMNotification

from bot.utils.config import keys
from bot.utils.util import get_fcm_topics_v1, get_fcm_topics_v2
from spacelaunchnow import config

logger = logging.getLogger('bot.notifications')


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
            if launch.mission is not None \
                    and launch.mission.orbit is not None \
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

            if launch.mission is not None \
                    and launch.mission.orbit is not None \
                    and launch.mission.orbit.name is not None:
                contents = '%s is in flight to %s!' % (launch.rocket.configuration.name, launch.mission.orbit.name)
            else:
                contents = '%s is in flight!' % launch.rocket.configuration.name

        elif notification_type == 'webcastLive':

            if launch.mission is not None and launch.mission.name is not None :
                contents = '%s %s webcast is live!' % (launch.rocket.configuration.name, launch.mission.name)
            else:
                contents = '%s webcast is live!' % launch.rocket.configuration.name

        else:
            launch_time = launch.net
            contents = 'Launch attempt from %s on %s at %s.' % (launch.pad.location.name,
                                                                launch_time.strftime("%A, %B %d"),
                                                                launch_time.strftime("%H:%M UTC"))

        # Create a notification
        topics_v1 = get_fcm_topics_v1(launch,
                                      notification_type=notification_type,
                                      debug=self.DEBUG)
        topics_v2 = get_fcm_topics_v2(launch,
                                      notification_type=notification_type,
                                      debug=self.DEBUG)
        if len(launch.vid_urls.all()) > 0:
            webcast = True
        else:
            webcast = False
        image = ''
        if launch.rocket.configuration.launch_agency.image_url:
            image = launch.rocket.configuration.launch_agency.image_url.url
        elif launch.rocket.configuration.launch_agency.legacy_image_url:
            image = launch.rocket.configuration.launch_agency.legacy_image_url
        v1_data = {"silent": True,
                   "background": True,
                   "launch_id": launch.launch_library_id,
                   "launch_uuid": str(launch.id),
                   "launch_name": launch.name,
                   "launch_image": image,
                   "launch_net": launch.net.strftime("%B %d, %Y %H:%M:%S %Z"),
                   "launch_location": launch.pad.location.name,
                   "notification_type": notification_type,
                   "webcast": webcast
                   }
        v2_data = {"notification_type": notification_type,
                   "launch_id": launch.launch_library_id,
                   "launch_uuid": str(launch.id),
                   "launch_name": launch.name,
                   "launch_image": image,
                   "launch_net": launch.net.strftime("%B %d, %Y %H:%M:%S %Z"),
                   "launch_location": launch.pad.location.name,
                   "webcast": webcast
                   }
        time_since_last_notification = None
        if notification.last_notification_sent is not None:
            time_since_last_notification = datetime.now(tz=pytz.utc) - notification.last_notification_sent
        if time_since_last_notification is not None and time_since_last_notification.total_seconds() < 30 and not self.DEBUG:
            logger.info('Cannot send notification - too soon since last notification!')
        else:
            logger.info('----------------------------------------------------------')
            logger.info('Sending notification - %s' % contents)
            notification.last_notification_sent = datetime.now(tz=pytz.utc)
            notification.save()
            push_service = FCMNotification(api_key=keys['FCM_KEY'])
            flutter_topics = get_fcm_topics_v1(launch,
                                               debug=self.DEBUG,
                                               flutter=True,
                                               notification_type=notification_type)
            flutter_topics_v2 = get_fcm_topics_v2(launch,
                                                  notification_type=notification_type,
                                                  debug=self.DEBUG,
                                                  flutter=True)

            # Send notifications to SLN Android before 3.0.0
            # Catch any issue with sending notification.
            if launch.launch_library_id is not None and launch.launch_library:
                try:
                    logger.info('Notification v1 Data - %s' % v1_data)
                    logger.info('Topic Data v1- %s' % topics_v1)
                    android_result_v1 = push_service.notify_topic_subscribers(data_message=v1_data,
                                                                              condition=topics_v1,
                                                                              time_to_live=86400, )
                    logger.info(android_result_v1)
                except Exception as e:
                    logger.error(e)

            # Send notifications to SLN Android after 3.0.0
            # Catch any issue with sending notification.
            try:
                logger.info('Notification v2 Data - %s' % v1_data)
                logger.info('Topic Data v2- %s' % topics_v1)
                android_result_v2 = push_service.notify_topic_subscribers(data_message=v2_data,
                                                                          condition=topics_v2,
                                                                          time_to_live=86400, )
                logger.info(android_result_v2)
            except Exception as e:
                logger.error(e)

            try:
                logger.info('Flutter v1 Notification')
                logger.info('Notification v1 Data - %s' % v1_data)
                logger.info('Flutter Topic v1- %s' % flutter_topics)
                flutter_result = push_service.notify_topic_subscribers(data_message=v1_data,
                                                                       condition=flutter_topics,
                                                                       time_to_live=86400,
                                                                       message_title=launch.name,
                                                                       message_body=contents)
                logger.debug(flutter_result)
            except Exception as e:
                logger.error(e)

            try:
                logger.info('Flutter v2 Notification')
                logger.info('Notification v2 Data - %s' % v2_data)
                logger.info('Flutter Topic v2- %s' % flutter_topics_v2)
                flutter_result = push_service.notify_topic_subscribers(data_message=v2_data,
                                                                       condition=flutter_topics_v2,
                                                                       time_to_live=86400,
                                                                       message_title=launch.name,
                                                                       message_body=contents)
                logger.debug(flutter_result)
            except Exception as e:
                logger.error(e)
            logger.info('----------------------------------------------------------')
