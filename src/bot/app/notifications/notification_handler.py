import logging
from datetime import datetime

import pytz
from api.models import Article, Events, Launch
from django.core.cache import cache
from pyfcm import FCMNotification

from bot.models import LaunchNotificationRecord
from bot.utils.util import (
    get_fcm_all_topics_v3,
    get_fcm_not_strict_topics_v3,
    get_fcm_strict_topics_v3,
    get_flutter_topics_v3,
)
from spacelaunchnow import settings

logger = logging.getLogger(__name__)


# TODO refactor to separate files/modules per version


class NotificationHandler:
    def __init__(self, debug=settings.DEBUG):
        self.DEBUG = debug
        self.api_key = settings.FCM_KEY

        if self.api_key is None and not settings.DEBUG:
            raise Exception("No FCM_KEY provided.")

        if settings.DEBUG:
            self.api_key = None

    def send_notification(self, launch: Launch, notification_type: str, notification: LaunchNotificationRecord):
        current_time = datetime.now(tz=pytz.utc)
        launch_time = launch.net
        diff = int((launch_time - current_time).total_seconds())
        cache_key = str(launch.id) + notification_type
        launch_cooldown = cache.get(cache_key)
        global_cooldown = cache.get(notification_type)
        logger.info(f"Launch Cooldown: {launch_cooldown} Global Cooldown: {global_cooldown}")
        if launch_cooldown or global_cooldown:
            logger.error(
                f"Notification cooldown window for {launch.id} - Launch: {launch_cooldown} Global: {global_cooldown}"
            )
            return
        logger.info(f"Creating {notification_type} notification for {launch.name}")
        cache.set(cache_key, f"ID: {launch.id} Net: {launch.net} Type: {notification_type}", 60)
        cache.set(notification_type, f"ID: {launch.id} Net: {launch.net} Type: {notification_type}", 60)
        if notification_type == "netstampChanged":
            if launch.status.id == 1:
                launch_date = launch.net.strftime("%A, %B %d")
                launch_time_utc = launch.net.strftime("%H:%M UTC")
                contents = f"UPDATE: New launch attempt scheduled on {launch_date} at {launch_time_utc}."
            elif launch.status.id == 2 or launch.status.id == 5 or launch.status.id == 8:
                contents = "UPDATE: Launch has slipped, new launch date is unconfirmed."
            else:
                logger.warning("Invalid state for sending a notification - Launch: %s" % launch)
                return
        elif notification_type == "tenMinutes":
            minutes = round(diff / 60)
            if minutes == 0:
                minutes = "less than one"
            if launch.status.id == 1:
                contents = f"Launch attempt from {launch.pad.location.name} in {minutes} minute(s)."
            else:
                logger.warning("Invalid state for sending a notification - Launch: %s" % launch)
                return
        elif notification_type == "oneMinute":
            if launch.status.id == 1:
                contents = "Launch attempt from %s in less than one minute." % launch.pad.location.name
            else:
                logger.warning("Invalid state for sending a notification - Launch: %s" % launch)
                return
        elif notification_type == "twentyFourHour":
            hours = round(diff / 60 / 60)
            if hours == 23:
                hours = 24
            if launch.status.id == 1:
                contents = f"Launch attempt from {launch.pad.location.name} in {hours} hours."
            elif launch.status.id == 2 or launch.status.id == 5:
                contents = f"Might be launching from {launch.pad.location.name} in {hours} hours."
            else:
                logger.warning("Invalid state for sending a notification - Launch: %s" % launch)
                return
        elif notification_type == "oneHour":
            if launch.status.id == 1:
                contents = "Launch attempt from %s in one hour." % launch.pad.location.name
            elif launch.status.id == 2 or launch.status.id == 5:
                contents = "Might be launching from %s in one hour." % launch.pad.location.name
            else:
                logger.error("Invalid state for sending a notification - Launch: %s" % launch)
                return
        elif notification_type == "success":
            if (
                launch.mission is not None
                and launch.mission.orbit is not None
                and launch.mission.orbit.name is not None
            ):
                orbit_name = launch.mission.orbit.name
                launch_service_provider_name = launch.launch_service_provider.name
                contents = f"Successful launch to {orbit_name} by {launch_service_provider_name}"
            else:
                contents = "Successful launch by %s" % launch.launch_service_provider.name

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
                    rocket_name = launch.rocket.configuration.name
                    orbit_name = launch.mission.orbit.name
                    contents = f"Liftoff! {rocket_name} is in a {orbit_name} flight!"
                else:
                    rocket_name = launch.rocket.configuration.name
                    orbit_name = launch.mission.orbit.name
                    contents = f"Liftoff! {rocket_name} is in flight to {orbit_name}!"
            else:
                contents = "Liftoff! %s is in flight!" % launch.rocket.configuration.name

        elif notification_type == "webcastLive":
            if launch.mission is not None and launch.mission.name is not None:
                contents = f"{launch.rocket.configuration.name} {launch.mission.name} webcast is live!"
            else:
                contents = "%s webcast is live!" % launch.rocket.configuration.name

        else:
            launch_time = launch.net
            location_name = launch.pad.location.name
            launch_date = launch_time.strftime("%A, %B %d")
            launch_time_utc = launch_time.strftime("%H:%M UTC")
            contents = f"Launch attempt from {location_name} on {launch_date} at {launch_time_utc}."

        time_since_last_notification = None
        if notification.last_notification_sent is not None:
            time_since_last_notification = datetime.now(tz=pytz.utc) - notification.last_notification_sent
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
            push_service = FCMNotification(api_key=self.api_key)
            self.send_v3_notification(launch, notification_type, push_service, contents)

            logger.info("----------------------------------------------------------")

    def send_v3_notification(
        self, launch: Launch, notification_type: str, push_service: FCMNotification, contents: str
    ):
        webcast = len(launch.vid_urls.all()) > 0
        image = ""
        if launch.image:
            image = launch.image.image.url
        elif launch.launch_service_provider and launch.launch_service_provider.image:
            image = launch.launch_service_provider.image.image.url

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
        all_topics = get_fcm_all_topics_v3(debug=self.DEBUG, notification_type=notification_type)
        strict_topics = get_fcm_strict_topics_v3(launch, debug=self.DEBUG, notification_type=notification_type)
        not_strict_topics = get_fcm_not_strict_topics_v3(launch, debug=self.DEBUG, notification_type=notification_type)
        self.send_notif_v3(push_service, data, all_topics)
        self.send_notif_v3(push_service, data, strict_topics)
        self.send_notif_v3(push_service, data, not_strict_topics)
        logger.info(f"Topics:\n\nALL: {all_topics}\nStrict: {strict_topics}\nNot Strict: {not_strict_topics}")
        # Reusing topics from v2 - not doing strict topics
        flutter_topics_v3 = get_flutter_topics_v3(
            launch, notification_type=notification_type, debug=self.DEBUG, flutter=True
        )
        self.send_notif_v3(push_service, data, flutter_topics_v3, message_title=launch.name, message_body=contents)

    def send_notif_v3(self, push_service, data, topics, message_title=None, message_body=None):
        # Send notifications to SLN Android > v3.7.0
        # Catch any issue with sending notification.
        try:
            logger.info("Notification v3 Data - %s" % data)
            logger.info("Topic Data v3- %s" % topics)
            results = push_service.notify_topic_subscribers(
                data_message=data,
                condition=topics,
                time_to_live=86400,
                message_title=message_title,
                message_body=message_body,
            )
            logger.info(results)
        except Exception as e:
            logger.error(e)

    def send_custom_ios_v3(self, pending):
        data = self.get_json_data(pending)

        if not self.DEBUG:
            flutter_topics = "'flutter_production_v3' in topics && 'custom' in topics"
        else:
            flutter_topics = "'flutter_debug_v3' in topics && 'custom' in topics"

        push_service = FCMNotification(api_key=self.api_key)

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

    def send_custom_android_v3(self, pending):
        data = self.get_json_data(pending)

        if not self.DEBUG:
            topics = "'prod_v3' in topics && 'custom' in topics"
        else:
            topics = "'debug_v3' in topics && 'custom' in topics"

        push_service = FCMNotification(api_key=self.api_key)

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
            if launch.image:
                image = launch.image.image.url
            elif launch.launch_service_provider and launch.launch_service_provider.image:
                image = launch.launch_service_provider.image.image.url

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
            if event.image and hasattr(event.image.image, "url"):
                feature_image = event.image.image.url
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
                        "news_url": event.info_urls.first(),
                        "video_url": event.vid_urls.first(),
                        "webcast_live": event.webcast_live,
                        "feature_image": feature_image,
                    },
                }
            )
        return data
