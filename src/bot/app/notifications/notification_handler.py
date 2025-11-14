import logging
import uuid
from dataclasses import dataclass
from datetime import datetime

import pytz
from api.models import Article, Events, Launch
from discord_webhook import DiscordEmbed, DiscordWebhook
from django.core.cache import cache

from bot.app.notification_service import NotificationService
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
from spacelaunchnow import settings

logger = logging.getLogger(__name__)


@dataclass
class NotificationResult:
    notification_type: str
    topics: str
    result: str | None
    analytics_label: str
    error: Exception | None


# TODO refactor to separate files/modules per version
class NotificationHandler(NotificationService):
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
        elif launch.launch_service_provider and launch.launch_service_provider.image:
            image = launch.launch_service_provider.image.image.url

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

        self.notify_discord([all_result, strict_result, not_strict_result, flutter_result, v4_result], data)

    def send_debug_notif(self):
        if self.DEBUG:
            topics = "'debug_v3' in topics && 'newZealand' in topics"  # noqa: E501
            generated = str(uuid.uuid4())
            analytics_label = "debug_test_topics_{generated}"

            results = self.fcm.notify(
                topic_condition=topics,
                notification_title="Test Notification",
                notification_body=f"{generated}\n{topics}",
                android_config={"priority": "high", "collapse_key": generated, "ttl": "86400s"},
                fcm_options={"analytics_label": analytics_label},
            )

            logger.info(f"NOTIF: {results} - {generated}")
            self.notify_discord(
                [
                    NotificationResult(
                        notification_type="Debug", topics=topics, analytics_label=analytics_label, result=results
                    )
                ],
                data=None,
            )

    def send_notif_v3(
        self, data, topics, message_title=None, message_body=None, analytics_label: str = None
    ) -> NotificationResult:
        try:
            logger.info(f"Notification v3 Data - {data}")
            logger.info(f"Topic Data v3- {topics}")
            results = self.fcm.notify(
                data_payload=data,
                topic_condition=topics,
                notification_title=message_title,
                notification_body=message_body,
                fcm_options={"analytics_label": analytics_label},
                android_config={"priority": "high", "collapse_key": data["launch_uuid"], "ttl": "86400s"},
                timeout=240,
            )
            logger.info(results)
            return NotificationResult(
                notification_type=data["notification_type"],
                topics=topics,
                result=results,
                analytics_label=analytics_label,
                error=None,
            )
        except Exception as e:
            logger.error(e)
            return NotificationResult(
                notification_type=data["notification_type"],
                topics=topics,
                result=results,
                analytics_label=analytics_label,
                error=e,
            )

    def send_notif_v3_5(
        self, data, topics, message_title=None, message_body=None, analytics_label: str = None
    ) -> NotificationResult:
        try:
            logger.info(f"Notification v3.5 Custom Data - {data}")
            logger.info(f"Topic Data v3.5- {topics}")
            results = self.fcm.notify(
                notification_title=message_title,
                notification_body=f"{message_body} {topics if self.DEBUG else ''}",
                notification_image=data["launch_image"],
                data_payload=data,
                topic_condition=topics,
                # Remove notification_title and notification_body to ensure custom handling
                fcm_options={"analytics_label": analytics_label},
                android_config={"priority": "high", "collapse_key": data["launch_uuid"], "ttl": "86400s"},
                timeout=240,
            )
            logger.info(results)
            return NotificationResult(
                notification_type=data["notification_type"],
                topics=topics,
                result=results,
                analytics_label=analytics_label,
                error=None,
            )
        except Exception as e:
            logger.error(e)
            return NotificationResult(
                notification_type=data["notification_type"],
                topics=topics,
                result=results,
                analytics_label=analytics_label,
                error=e,
            )

    def send_notif_v4(
        self, data, topics, message_title=None, message_body=None, analytics_label: str = None
    ) -> NotificationResult:
        try:
            logger.info(f"Notification v4 Data - {data}")
            logger.info(f"Topic Data v4 - {topics}")

            results = self.fcm.notify(
                data_payload=data,
                topic_condition=topics,
                notification_title=message_title,
                notification_body=message_body,
                fcm_options={"analytics_label": analytics_label},
                android_config={"priority": "high", "collapse_key": data["launch_uuid"], "ttl": "86400s"},
            )
            logger.info(results)
            return NotificationResult(
                notification_type=data["notification_type"],
                topics=topics,
                result=results,
                analytics_label=analytics_label,
                error=None,
            )
        except Exception as e:
            logger.error(e)
            return NotificationResult(
                notification_type=data["notification_type"],
                topics=topics,
                result=None,
                analytics_label=analytics_label,
                error=e,
            )

    def send_custom_ios_v3(self, pending) -> NotificationResult:
        data = self.get_json_data(pending)
        label = "notification_custom_ios"

        if not self.DEBUG:
            flutter_topics = "'flutter_production_v3' in topics && 'custom' in topics"
        else:
            flutter_topics = "'flutter_debug_v3' in topics && 'custom' in topics"

        logger.info("----------------------------------------------------------")
        logger.info(f"Sending iOS Custom Flutter notification - {pending.title}")
        try:
            logger.info(f"Custom Notification Data - {data}")
            logger.info(f"Topics - {flutter_topics}")
            flutter_results = self.fcm.notify(
                data_payload=data,
                topic_condition=flutter_topics,
                notification_title=pending.title,
                notification_body=pending.message,
                fcm_options={"analytics_label": label},
                android_config={"priority": "high", "collapse_key": data["launch_uuid"], "ttl": "86400s"},
                timeout=240,
            )
            logger.info(flutter_results)
            return NotificationResult(
                notification_type=data["notification_type"],
                topics=flutter_topics,
                result=flutter_results,
                analytics_label=label,
                error=None,
            )
        except Exception as e:
            logger.error(e)
            self.notify_discord(data=data, topics=flutter_topics, analytics_label=label, error=e)
            return NotificationResult(
                notification_type=data["notification_type"],
                topics=flutter_topics,
                result=None,
                analytics_label=label,
                error=e,
            )

    def send_custom_android_v3(self, pending) -> NotificationResult:
        data = self.get_json_data(pending)
        label = "notification_custom_android"

        if not self.DEBUG:
            topics = "'prod_v3' in topics && 'custom' in topics"
        else:
            topics = "'debug_v3' in topics && 'custom' in topics"

        logger.info("----------------------------------------------------------")
        logger.info(f"Sending Android Custom notification - {pending.title}")
        try:
            logger.info(f"Custom Notification Data - {data}")
            logger.info(f"Topics - {topics}")
            android_result = self.fcm.notify(
                data_payload=data,
                topic_condition=topics,
                fcm_options={"analytics_label": label},
                android_config={"priority": "high", "collapse_key": data["launch_uuid"], "ttl": "86400s"},
                timeout=240,
            )
            logger.info(android_result)
            return NotificationResult(
                notification_type=data["notification_type"],
                topics=topics,
                result=android_result,
                analytics_label=label,
                error=None,
            )
        except Exception as e:
            logger.error(e)
            return NotificationResult(
                notification_type=data["notification_type"],
                topics=topics,
                result=None,
                analytics_label=label,
                error=e,
            )

    def get_json_data(self, pending):
        data = {
            "notification_type": "custom",
            "click_action": "FLUTTER_NOTIFICATION_CLICK",
            "title": pending.title,
            "message": pending.message,
            "notification_id": str(pending.id),
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
                        "launch_id": str(launch.id),
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
                        "webcast_live": str(event.webcast_live),
                        "feature_image": feature_image,
                    },
                }
            )
        return data

    def notify_discord(
        self,
        notification_results: list[NotificationResult] = None,
        data: dict[str, str] = None,
    ) -> None:
        launch_name = data.get("launch_name", "Unknown") if data else "Unknown"
        launch_uuid = data.get("launch_uuid", "Unknown") if data else "Unknown"
        launch_net = data.get("launch_net", "Unknown") if data else "Unknown"
        launch_location = data.get("launch_location", "Unknown") if data else "Unknown"
        launch_image = data.get("launch_image") if data else None

        # Set up the webhook
        webhook = DiscordWebhook(
            url=settings.DISCORD_WEBHOOK,
            username="Notification Tracker",
            avatar_url="https://thespacedevs-prod.nyc3.digitaloceanspaces.com/static/home/img/launcher.png",
        )

        description = ""
        for notification_result in notification_results:
            fcm_result = {"title": None, "description": None}
            if notification_result.error:
                fcm_result["title"] = "Error"
                fcm_result["description"] = f"`{notification_result.error}`"
            if notification_result.result:
                fcm_result["title"] = "Result"
                fcm_result["description"] = f"`{notification_result.result}`"
            if notification_result.result and notification_result.error:
                fcm_result["title"] = "Result w/ Error"
                fcm_result["description"] = f"`{notification_result.result}`\n`{notification_result.error}`"

            description += (
                f"**Notification Type:** `{notification_result.notification_type}`\n"
                f"**Analytics Label:** `{notification_result.analytics_label}`\n"
                f"**Topics:** `{notification_result.topics}`\n"
                f"**{fcm_result['title']}:** {fcm_result['description']}\n"
                f"{'-' * 50}\n"
            )

        # Create the Embed
        embed = DiscordEmbed(
            title=f"🚀 {launch_name} 🚀",
            description=description,
            color="03b2f8",
        )

        # Add fields for relevant data
        embed.add_embed_field(name="Launch Name", value=launch_name, inline=False)
        embed.add_embed_field(name="Launch UUID", value=launch_uuid, inline=False)
        embed.add_embed_field(name="Launch NET", value=launch_net, inline=False)
        embed.add_embed_field(name="Launch Location", value=launch_location, inline=False)

        # Add an image for the launch if available
        if launch_image is not None:
            embed.set_thumbnail(url=launch_image)

        # Add footer with timestamp
        embed.set_footer(text="Space Launch Now - Notification Tracker")
        embed.set_timestamp()

        # Add the embed to the webhook
        webhook.add_embed(embed)

        # Execute the webhook (send the notification)
        response = webhook.execute()
        logger.info(f"Discord Notification Response: {response}")
