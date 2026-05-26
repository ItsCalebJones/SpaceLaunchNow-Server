"""Custom notification handlers for iOS and Android."""

import logging

from api.models import Article, Events, Launch

from bot.app.notifications.base import NotificationResult
from bot.utils.util import get_fcm_v5_android_topic, get_fcm_v5_ios_topic

logger = logging.getLogger(__name__)


class CustomNotificationMixin:
    """Mixin for custom notification methods (iOS/Android)."""

    def _build_v5_custom_data(self, pending) -> dict:
        """Build V5-compatible flat data payload for custom admin notifications.

        V5 payloads use flat key-value strings (FCM requirement). The optional
        launch/news/event reference collapses to target_type + target_id (+
        target_url for news) so the KMP app can deep-link on tap. The
        notification_type is always "custom" — checked FIRST by KMP so a custom
        notification referencing an event is not mis-detected as an event.
        """
        target_type = "none"
        target_id = ""
        target_url = ""
        custom_image = ""

        if pending.launch_id is not None:
            launch = Launch.objects.get(id=pending.launch_id)
            image = ""
            if launch.image:
                image = launch.image.image.url
            elif launch.launch_service_provider and launch.launch_service_provider.image:
                image = launch.launch_service_provider.image.image.url
            target_type = "launch"
            target_id = str(launch.id)
            custom_image = image
        elif pending.news_id is not None:
            article = Article.objects.get(id=pending.news_id)
            target_type = "news"
            target_id = str(article.id)
            target_url = article.link or ""
            custom_image = article.featured_image or ""
        elif pending.event_id is not None:
            event = Events.objects.get(id=pending.event_id)
            feature_image = ""
            if event.image and hasattr(event.image.image, "url"):
                feature_image = event.image.image.url
            target_type = "event"
            target_id = str(event.id)
            custom_image = feature_image

        return {
            "notification_type": "custom",
            "title": pending.title,
            "body": pending.message,
            "custom_id": str(pending.id),
            "target_type": target_type,
            "target_id": target_id,
            "target_url": target_url,
            "custom_image": custom_image,
        }

    def _send_v5_custom_android(self, pending) -> None:
        """Send a custom admin notification to the V5 Android topic (data-only)."""
        v5_data = self._build_v5_custom_data(pending)
        android_topics = get_fcm_v5_android_topic(debug=self.DEBUG)
        logger.info("----------------------------------------------------------")
        logger.info("V5 Android Custom Notification")
        logger.info(f"Notification Data: {v5_data}")
        logger.info(f"Topics: {android_topics}")
        try:
            android_result = self.fcm.notify(
                data_payload=v5_data,
                topic_condition=android_topics,
                notification_title=None,
                notification_body=None,
                fcm_options={"analytics_label": f"v5_android_custom_{v5_data['custom_id']}"},
                android_config={
                    "priority": "high",
                    "collapse_key": f"custom_{v5_data['custom_id']}",
                    "ttl": "86400s",
                },
                timeout=240,
            )
            logger.info(f"V5 Android Custom Result: {android_result}")
        except Exception as e:
            logger.error(f"V5 Android Custom Notification Error: {e}")
        logger.info("----------------------------------------------------------")

    def _send_v5_custom_ios(self, pending) -> None:
        """Send a custom admin notification to the V5 iOS topic (alert + mutable-content)."""
        v5_data = self._build_v5_custom_data(pending)
        ios_topics = get_fcm_v5_ios_topic(debug=self.DEBUG)
        logger.info("----------------------------------------------------------")
        logger.info("V5 iOS Custom Notification")
        logger.info(f"Notification Data: {v5_data}")
        logger.info(f"Topics: {ios_topics}")
        try:
            ios_result = self.fcm.notify(
                data_payload=v5_data,
                topic_condition=ios_topics,
                notification_title=v5_data["title"],
                notification_body=v5_data["body"],
                fcm_options={"analytics_label": f"v5_ios_custom_{v5_data['custom_id']}"},
                apns_config={
                    "headers": {
                        "apns-priority": "10",
                    },
                    "payload": {
                        "aps": {
                            "mutable-content": 1,
                        },
                    },
                },
                timeout=240,
            )
            logger.info(f"V5 iOS Custom Result: {ios_result}")
        except Exception as e:
            logger.error(f"V5 iOS Custom Notification Error: {e}")
        logger.info("----------------------------------------------------------")

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
                        "news_url": getattr(event.info_urls.first(), "info_url", None),
                        "video_url": getattr(event.vid_urls.first(), "vid_url", None),
                        "webcast_live": str(event.webcast_live),
                        "feature_image": feature_image,
                    },
                }
            )
        return data
