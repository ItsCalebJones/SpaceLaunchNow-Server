"""Main notification handler combining all version mixins."""

import logging
from datetime import datetime

import pytz
from api.models import Launch
from django.core.cache import cache

from bot.app.notification_service import NotificationService
from bot.app.notifications.base import NotificationResult
from bot.app.notifications.custom import CustomNotificationMixin
from bot.app.notifications.debug import DebugNotificationMixin
from bot.app.notifications.discord import DiscordNotificationMixin
from bot.app.notifications.v3 import V3NotificationMixin
from bot.app.notifications.v4 import V4NotificationMixin
from bot.app.notifications.v5 import V5NotificationMixin
from bot.models import LaunchNotificationRecord
from bot.utils.util import (
    get_agency_topic,
    get_fcm_all_topics_v3,
    get_fcm_not_strict_topics_v3,
    get_fcm_strict_topics_v3,
    get_fcm_v4_topic,
    get_flutter_topics_v3,
    get_location_topic,
)

logger = logging.getLogger(__name__)

# Re-export NotificationResult for backward compatibility
__all__ = ["NotificationHandler", "NotificationResult"]


class NotificationHandler(
    V3NotificationMixin,
    V4NotificationMixin,
    V5NotificationMixin,
    CustomNotificationMixin,
    DiscordNotificationMixin,
    DebugNotificationMixin,
    NotificationService,
):
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
                logger.warning(f"{notification_type} Invalid state for sending a notification - Launch: {launch}")
                return
        elif notification_type == "tenMinutes":
            minutes = round(diff / 60)
            if minutes == 0:
                minutes = "less than one"
            if launch.status.id == 1:
                contents = f"Launch attempt from {launch.pad.location.name} in {minutes} minute(s)."
            else:
                logger.warning(f"{notification_type} Invalid state for sending a notification - Launch: {launch}")
                return
        elif notification_type == "oneMinute":
            if launch.status.id == 1:
                contents = f"Launch attempt from {launch.pad.location.name} in less than one minute."
            else:
                logger.warning(f"{notification_type} Invalid state for sending a notification - Launch: {launch}")
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
                logger.warning(f"{notification_type} Invalid state for sending a notification - Launch: {launch}")
                return
        elif notification_type == "oneHour":
            if launch.status.id == 1:
                contents = f"Launch attempt from {launch.pad.location.name} in one hour."
            elif launch.status.id == 2 or launch.status.id == 5:
                contents = f"Might be launching from {launch.pad.location.name} in one hour."
            else:
                logger.warning(f"{notification_type} Invalid state for sending a notification - Launch: {launch}")
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
                contents = f"Successful launch by {launch.launch_service_provider.name}"

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
                contents = f"Liftoff! {launch.rocket.configuration.name} is in flight!"

        elif notification_type == "webcastLive":
            if launch.mission is not None and launch.mission.name is not None:
                contents = f"{launch.rocket.configuration.name} {launch.mission.name} webcast is live!"
            else:
                contents = f"{launch.rocket.configuration.name} webcast is live!"

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
            logger.info(f"Sending notification - {contents}")
            notification.last_notification_sent = datetime.now(tz=pytz.utc)
            notification.save()
            self.send_v3_notification(launch, notification_type, contents)

            logger.info("----------------------------------------------------------")

    def send_v3_notification(self, launch: Launch, notification_type: str, contents: str):
        webcast = len(launch.vid_urls.all()) > 0

        image = ""
        if launch.image:
            image = launch.image.image.url
        elif launch.rocket.configuration.image.image:
            image = launch.rocket.configuration.image.image.url
        elif launch.launch_service_provider and launch.launch_service_provider.image:
            image = launch.launch_service_provider.image.image.url
        # .
        data = {
            "notification_type": notification_type,
            "launch_id": str(launch.id),
            "launch_uuid": str(launch.id),
            "launch_name": launch.name,
            "launch_image": image,
            "launch_net": launch.net.strftime("%B %d, %Y %H:%M:%S %Z"),
            "launch_location": launch.pad.location.name,
            "webcast": str(webcast),
        }

        all_result = self.send_notif_v3_5(
            data=data,
            topics=get_fcm_all_topics_v3(debug=self.DEBUG, notification_type=notification_type),
            message_title=launch.name,
            message_body=contents,
            analytics_label=f"notification_all_{data['launch_uuid']}",
        )

        strict_result = self.send_notif_v3_5(
            data=data,
            topics=get_fcm_strict_topics_v3(launch, debug=self.DEBUG, notification_type=notification_type),
            message_title=launch.name,
            message_body=contents,
            analytics_label=f"notification_strict_{data['launch_uuid']}",
        )

        not_strict_result = self.send_notif_v3_5(
            data=data,
            topics=get_fcm_not_strict_topics_v3(launch, debug=self.DEBUG, notification_type=notification_type),
            message_title=launch.name,
            message_body=contents,
            analytics_label=f"notification_not_strict_{data['launch_uuid']}",
        )

        flutter_result = self.send_notif_v3(
            data=data,
            topics=get_flutter_topics_v3(launch, notification_type=notification_type, debug=self.DEBUG, flutter=True),
            message_title=launch.name,
            message_body=contents,
            analytics_label=f"notification_flutter_{data['launch_uuid']}",
        )

        # Send v4 notification with client-side filtering
        v4_data = {
            "notification_type": notification_type,
            "launch_id": str(launch.id),
            "launch_uuid": str(launch.id),
            "launch_name": launch.name,
            "launch_image": image,
            "launch_net": launch.net.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "launch_location": launch.pad.location.name,
            "webcast": str(webcast),
            "webcast_live": str(launch.webcast_live),
            "agency_id": str(get_agency_topic(launch)),
            "location_id": str(get_location_topic(launch)),
        }

        v4_result = self.send_notif_v4(
            data=v4_data,
            topics=get_fcm_v4_topic(debug=self.DEBUG),
            message_title=None,
            message_body=None,
            analytics_label=f"notification_v4_{data['launch_uuid']}",
        )

        # Send v5 notifications with platform-specific messaging
        v5_results = self.send_v5_notification(
            launch=launch,
            notification_type=notification_type,
            contents=contents,
        )

        all_results = [all_result, strict_result, not_strict_result, flutter_result, v4_result] + v5_results
        self.notify_discord(all_results, data)
