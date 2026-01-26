"""Custom notification handlers for iOS and Android."""

import logging

from api.models import Article, Events, Launch

from bot.app.notifications.base import NotificationResult

logger = logging.getLogger(__name__)


class CustomNotificationMixin:
    """Mixin for custom notification methods (iOS/Android)."""

    def send_custom_ios_v3(self, pending) -> NotificationResult:
        """Send custom iOS Flutter notification."""
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
        """Send custom Android notification."""
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

    def get_json_data(self, pending) -> dict:
        """Build JSON data payload for custom notifications."""
        data = {
            "notification_type": "custom",
            "click_action": "FLUTTER_NOTIFICATION_CLICK",
            "title": pending.title,
            "message": pending.message,
            "notification_id": str(pending.id),
            "launch_uuid": str(pending.id),  # Used as collapse key
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
