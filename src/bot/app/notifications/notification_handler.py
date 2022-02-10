import logging
from datetime import datetime

import pytz
from api.models import Article, Events, Launch
from django.core.cache import cache
from pyfcm import FCMNotification

from bot.utils.util import (
    get_fcm_all_topics_v3,
    get_fcm_not_strict_topics_v3,
    get_fcm_strict_topics_v3,
    get_fcm_topics_v2,
)
from spacelaunchnow import config

logger = logging.getLogger("bot.notifications")


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
        cache_key = str(launch.id) + notification_type
        launch_cooldown = cache.get(cache_key)
        global_cooldown = cache.get(notification_type)
        if launch_cooldown or global_cooldown:
            logger.error(
                "Notification cooldown window for %s - Launch: %s Global: %s"
                % (launch.id, launch_cooldown, global_cooldown)
            )
            return
        logger.info(
            "Creating %s notification for %s" % (notification_type, launch.name)
        )
        cache.set(
            cache_key,
            "ID: %s Net: %s Type: %s" % (launch.id, launch.net, notification_type),
            60,
        )
        cache.set(
            notification_type,
            "ID: %s Net: %s Type: %s" % (launch.id, launch.net, notification_type),
            60,
        )
        if notification_type == "netstampChanged":
            if launch.status.id == 1:
                contents = "UPDATE: New launch attempt scheduled on %s at %s." % (
                    launch.net.strftime("%A, %B %d"),
                    launch.net.strftime("%H:%M UTC"),
                )
            elif launch.status.id == 2 or launch.status == 5:
                contents = "UPDATE: Launch has slipped, new launch date is unconfirmed."
            else:
                logger.error(
                    "Invalid state for sending a notification - Launch: %s" % launch
                )
                return
        elif notification_type == "tenMinutes":
            minutes = round(diff / 60)
            if minutes == 0:
                minutes = "less than one"
            if launch.status.id == 1:
                contents = "Launch attempt from %s in %s minute(s)." % (
                    launch.pad.location.name,
                    minutes,
                )
            else:
                logger.error(
                    "Invalid state for sending a notification - Launch: %s" % launch
                )
                return
        elif notification_type == "oneMinute":
            if launch.status.id == 1:
                contents = (
                    "Launch attempt from %s in less than one minute."
                    % launch.pad.location.name
                )
            else:
                logger.error(
                    "Invalid state for sending a notification - Launch: %s" % launch
                )
                return
        elif notification_type == "twentyFourHour":
            hours = round(diff / 60 / 60)
            if hours == 23:
                hours = 24
            if launch.status.id == 1:
                contents = "Launch attempt from %s in %s hours." % (
                    launch.pad.location.name,
                    hours,
                )
            elif launch.status.id == 2 or launch.status.id == 5:
                contents = "Might be launching from %s in %s hours." % (
                    launch.pad.location.name,
                    hours,
                )
            else:
                logger.error(
                    "Invalid state for sending a notification - Launch: %s" % launch
                )
                return
        elif notification_type == "oneHour":
            if launch.status.id == 1:
                contents = (
                    "Launch attempt from %s in one hour." % launch.pad.location.name
                )
            elif launch.status.id == 2 or launch.status.id == 5:
                contents = (
                    "Might be launching from %s in one hour." % launch.pad.location.name
                )
            else:
                logger.error(
                    "Invalid state for sending a notification - Launch: %s" % launch
                )
                return
        elif notification_type == "success":
            if (
                launch.mission is not None
                and launch.mission.orbit is not None
                and launch.mission.orbit.name is not None
            ):
                contents = "Successful launch to %s by %s" % (
                    launch.mission.orbit.name,
                    launch.launch_service_provider.name,
                )
            else:
                contents = (
                    "Successful launch by %s" % launch.launch_service_provider.name
                )

        elif notification_type == "failure":
            contents = "A launch failure has occurred."

        elif notification_type == "partial_failure":
            contents = "A partial launch failure has occurred."

        elif notification_type == "inFlight":

            if (
                launch.mission is not None
                and launch.mission.orbit is not None
                and launch.mission.orbit.name is not None
            ):
                if launch.mission.orbit.id == 15:
                    contents = "Liftoff! %s is in a %s flight!" % (
                        launch.rocket.configuration.name,
                        launch.mission.orbit.name,
                    )
                else:
                    contents = "Liftoff! %s is in flight to %s!" % (
                        launch.rocket.configuration.name,
                        launch.mission.orbit.name,
                    )
            else:
                contents = (
                    "Liftoff! %s is in flight!" % launch.rocket.configuration.name
                )

        elif notification_type == "webcastLive":

            if launch.mission is not None and launch.mission.name is not None:
                contents = "%s %s webcast is live!" % (
                    launch.rocket.configuration.name,
                    launch.mission.name,
                )
            else:
                contents = "%s webcast is live!" % launch.rocket.configuration.name

        else:
            launch_time = launch.net
            contents = "Launch attempt from %s on %s at %s." % (
                launch.pad.location.name,
                launch_time.strftime("%A, %B %d"),
                launch_time.strftime("%H:%M UTC"),
            )

        time_since_last_notification = None
        if notification.last_notification_sent is not None:
            time_since_last_notification = (
                datetime.now(tz=pytz.utc) - notification.last_notification_sent
            )
        if (
            time_since_last_notification is not None
            and time_since_last_notification.total_seconds() < 30
            and not self.DEBUG
        ):
            logger.info("Cannot send notification - too soon since last notification!")
        else:
            logger.info("----------------------------------------------------------")
            logger.info("Sending notification - %s" % contents)
            notification.last_notification_sent = datetime.now(tz=pytz.utc)
            notification.save()
            push_service = FCMNotification(api_key=config.keys["FCM_KEY"])
            self.send_v2_notification(launch, notification_type, push_service, contents)
            self.send_v3_notification(launch, notification_type, push_service, contents)

            logger.info("----------------------------------------------------------")

    def send_v2_notification(self, launch, notification_type, push_service, contents):
        flutter_topics_v2 = get_fcm_topics_v2(
            launch, notification_type=notification_type, debug=self.DEBUG, flutter=True
        )
        topics_v2 = get_fcm_topics_v2(
            launch, notification_type=notification_type, debug=self.DEBUG
        )

        if len(launch.vid_urls.all()) > 0:
            webcast = True
        else:
            webcast = False
        image = ""
        if launch.image_url:
            image = launch.image_url.url
        elif launch.launch_service_provider.image_url:
            image = launch.launch_service_provider.image_url.url
        elif launch.launch_service_provider.legacy_image_url:
            image = launch.launch_service_provider.legacy_image_url

        data = {
            "notification_type": notification_type,
            "launch_id": launch.launch_library_id,
            "launch_uuid": str(launch.id),
            "launch_name": launch.name,
            "launch_image": image,
            "launch_net": launch.net.strftime("%B %d, %Y %H:%M:%S %Z"),
            "launch_location": launch.pad.location.name,
            "webcast": webcast,
        }

        # Send notifications to SLN Android after 3.0.0
        # Catch any issue with sending notification.
        try:
            logger.info("Android v2 Notification")
            logger.info("Notification v2 Data - %s" % data)
            logger.info("Topic Data v2- %s" % topics_v2)
            android_result_v2 = push_service.notify_topic_subscribers(
                data_message=data,
                condition=topics_v2,
                time_to_live=86400,
            )
            logger.info(android_result_v2)
        except Exception as e:
            logger.error(e)

        try:
            logger.info("Flutter v2 Notification")
            logger.info("Notification v2 Data - %s" % data)
            logger.info("Flutter Topic v2- %s" % flutter_topics_v2)
            flutter_result = push_service.notify_topic_subscribers(
                data_message=data,
                condition=flutter_topics_v2,
                time_to_live=86400,
                message_title=launch.name,
                message_body=contents,
            )
            logger.debug(flutter_result)
        except Exception as e:
            logger.error(e)

    def send_v3_notification(self, launch, notification_type, push_service, contents):
        if len(launch.vid_urls.all()) > 0:
            webcast = True
        else:
            webcast = False
        image = ""
        if launch.image_url:
            image = launch.image_url.url
        elif launch.launch_service_provider.image_url:
            image = launch.launch_service_provider.image_url.url
        elif launch.launch_service_provider.legacy_image_url:
            image = launch.launch_service_provider.legacy_image_url

        data = {
            "notification_type": notification_type,
            "launch_id": launch.launch_library_id,
            "launch_uuid": str(launch.id),
            "launch_name": launch.name,
            "launch_image": image,
            "launch_net": launch.net.strftime("%B %d, %Y %H:%M:%S %Z"),
            "launch_location": launch.pad.location.name,
            "webcast": webcast,
        }
        all_topics = get_fcm_all_topics_v3(
            debug=self.DEBUG, notification_type=notification_type
        )
        strict_topics = get_fcm_strict_topics_v3(
            launch, debug=self.DEBUG, notification_type=notification_type
        )
        not_strict_topics = get_fcm_not_strict_topics_v3(
            launch, debug=self.DEBUG, notification_type=notification_type
        )
        self.send_android_notif_v3(push_service, data, all_topics)
        self.send_android_notif_v3(push_service, data, strict_topics)
        self.send_android_notif_v3(push_service, data, not_strict_topics)
        logger.info(
            "Topics:\n\nALL: %s\nStrict: %s\nNot Strict: %s"
            % (all_topics, strict_topics, not_strict_topics)
        )

    def send_android_notif_v3(self, push_service, data, topics):
        # Send notifications to SLN Android > v3.7.0
        # Catch any issue with sending notification.
        try:
            logger.info("Notification v3 Data - %s" % data)
            logger.info("Topic Data v3- %s" % topics)
            results = push_service.notify_topic_subscribers(
                data_message=data,
                condition=topics,
                time_to_live=86400,
            )
            logger.info(results)
        except Exception as e:
            logger.error(e)

    def send_custom_ios_v2(self, pending):
        data = self.get_json_data(pending)

        if not self.DEBUG:
            flutter_topics = "'flutter_production_v2' in topics && 'custom' in topics"
        else:
            flutter_topics = "'flutter_debug_v2' in topics && 'custom' in topics"

        push_service = FCMNotification(api_key=config.keys["FCM_KEY"])

        logger.info("----------------------------------------------------------")
        logger.info("Sending iOS Custom Flutter notification - %s" % pending.title)
        try:
            logger.info("Custom Notification Data - %s" % data)
            logger.info("Topics - %s" % flutter_topics)
            flutter_results = push_service.notify_topic_subscribers(
                data_message=data,
                condition=flutter_topics,
                time_to_live=86400,
                message_title=pending.title,
                message_body=pending.message,
            )
            logger.info(flutter_results)
        except Exception as e:
            logger.error(e)

        logger.info("----------------------------------------------------------")

    def send_custom_ios_v3(self, pending):
        data = self.get_json_data(pending)

        if not self.DEBUG:
            flutter_topics = "'flutter_production_v3' in topics && 'custom' in topics"
        else:
            flutter_topics = "'flutter_debug_v3' in topics && 'custom' in topics"

        push_service = FCMNotification(api_key=config.keys["FCM_KEY"])

        logger.info("----------------------------------------------------------")
        logger.info("Sending iOS Custom Flutter notification - %s" % pending.title)
        try:
            logger.info("Custom Notification Data - %s" % data)
            logger.info("Topics - %s" % flutter_topics)
            flutter_results = push_service.notify_topic_subscribers(
                data_message=data,
                condition=flutter_topics,
                time_to_live=86400,
                message_title=pending.title,
                message_body=pending.message,
            )
            logger.info(flutter_results)
        except Exception as e:
            logger.error(e)

        logger.info("----------------------------------------------------------")

    def send_custom_android_v2(self, pending):
        data = self.get_json_data(pending)

        if not self.DEBUG:
            topics = "'prod_v2' in topics && 'custom' in topics"
        else:
            topics = "'debug_v2' in topics && 'custom' in topics"

        push_service = FCMNotification(api_key=config.keys["FCM_KEY"])

        logger.info("----------------------------------------------------------")
        logger.info("Sending Android Custom notification - %s" % pending.title)
        try:
            logger.info("Custom Notification Data - %s" % data)
            logger.info("Topics - %s" % topics)
            android_result = push_service.notify_topic_subscribers(
                data_message=data,
                condition=topics,
                time_to_live=86400,
            )
            logger.info(android_result)
        except Exception as e:
            logger.error(e)

        logger.info("----------------------------------------------------------")

    def send_custom_android_v3(self, pending):
        data = self.get_json_data(pending)

        if not self.DEBUG:
            topics = "'prod_v3' in topics && 'custom' in topics"
        else:
            topics = "'debug_v3' in topics && 'custom' in topics"

        push_service = FCMNotification(api_key=config.keys["FCM_KEY"])

        logger.info("----------------------------------------------------------")
        logger.info("Sending Android Custom notification - %s" % pending.title)
        try:
            logger.info("Custom Notification Data - %s" % data)
            logger.info("Topics - %s" % topics)
            android_result = push_service.notify_topic_subscribers(
                data_message=data,
                condition=topics,
                time_to_live=86400,
            )
            logger.info(android_result)
        except Exception as e:
            logger.error(e)

        logger.info("----------------------------------------------------------")

    def get_json_data(self, pending):
        data = {
            "notification_type": "custom",
            "click_action": "FLUTTER_NOTIFICATION_CLICK",
            "title": pending.title,
            "message": pending.message,
        }

        if pending.launch_id is not None:
            launch = Launch.objects.get(id=pending.launch_id)

            image = ""
            if launch.image_url:
                image = launch.image_url.url
            elif launch.launch_service_provider.image_url:
                image = launch.launch_service_provider.image_url.url
            elif launch.launch_service_provider.legacy_image_url:
                image = launch.launch_service_provider.legacy_image_url

            data.update(
                {
                    "launch": {
                        "launch_id": launch.launch_library_id,
                        "launch_uuid": str(launch.id),
                        "launch_name": launch.name,
                        "launch_image": image,
                        "launch_net": launch.net.strftime("%B %d, %Y %H:%M:%S %Z"),
                        "launch_location": launch.pad.location.name,
                        "webcast": launch.webcast_live,
                    }
                }
            )

        if pending.news_id is not None:
            news = Article.objects.get(id=pending.news_id)

            data.update(
                {
                    "news": {
                        "id": news.id,
                        "news_site_long": news.news_site,
                        "title": news.title,
                        "url": news.link,
                        "featured_image": news.featured_image,
                    }
                }
            )

        if pending.event_id is not None:
            event = Events.objects.get(id=pending.event_id)

            feature_image = None
            if event.feature_image and hasattr(event.feature_image, "url"):
                feature_image = event.feature_image.url
            data.update(
                {
                    "event": {
                        "id": event.id,
                        "name": event.name,
                        "description": event.description,
                        "type": {
                            "id": event.type.id,
                            "name": event.type.name,
                        },
                        "date": event.date.strftime("%B %d, %Y %H:%M:%S %Z"),
                        "location": event.location,
                        "news_url": event.news_url,
                        "video_url": event.video_url,
                        "webcast_live": event.webcast_live,
                        "feature_image": feature_image,
                    },
                }
            )
        return data
