import json
import logging

from bot.app.notification_service import NotificationService
from bot.app.notifications.metrics import record_send
from bot.utils.util import get_fcm_v5_android_topic, get_fcm_v5_ios_topic

logger = logging.getLogger(__name__)


class NewsNotificationHandler(NotificationService):
    def send_notification(self, article):
        # V5-only. send_v3_notification is retained but no longer invoked.
        self._send_v5_notification(article)

    def send_to_social(self, article):
        # No-op placeholder. The original social-posting implementation (and its
        # SocialHandler) were removed in the LL-images rework. Kept as a stub so the
        # caller in EventTracker.check_news_item still resolves; reinstate posting
        # here if/when we return to publishing articles to social platforms.
        return None

    def _build_v5_news_data(self, article):
        """Build V5-compatible flat data payload for featured-news notifications.

        V5 payloads use flat key-value strings (FCM requirement) with an
        'article_id' field so the KMP app can detect this is a news notification
        (it carries no lsp_id and no event_id) and open the article.
        """
        return {
            "notification_type": "featured_news",
            "title": f"New article via {article.news_site}",
            "body": article.title,
            "article_id": str(article.id),
            "article_title": article.title,
            "article_news_site": article.news_site,
            "article_url": article.link,
            "article_image": article.featured_image or "",
        }

    def _send_v5_notification(self, article):
        """Send featured-news notifications to V5 Android and iOS topics."""
        v5_data = self._build_v5_news_data(article)

        # V5 Android (data-only)
        android_topics = get_fcm_v5_android_topic(debug=self.DEBUG)
        logger.info("----------------------------------------------------------")
        logger.info("V5 Android News Notification")
        logger.info(f"Notification Data: {v5_data}")
        logger.info(f"Topics: {android_topics}")
        try:
            android_result = self.fcm.notify(
                data_payload=v5_data,
                topic_condition=android_topics,
                notification_title=None,
                notification_body=None,
                fcm_options={"analytics_label": f"v5_android_news_{v5_data['article_id']}"},
                android_config={
                    "priority": "high",
                    "collapse_key": f"news_{v5_data['article_id']}",
                    "ttl": "86400s",
                },
                timeout=240,
            )
            logger.info(f"V5 Android News Result: {android_result}")
            record_send(platform="android", category="news", success=True, result=android_result)
        except Exception as e:
            logger.error(f"V5 Android News Notification Error: {e}")
            record_send(platform="android", category="news", success=False)
        logger.info("----------------------------------------------------------")

        # V5 iOS (alert with mutable-content)
        ios_topics = get_fcm_v5_ios_topic(debug=self.DEBUG)
        logger.info("----------------------------------------------------------")
        logger.info("V5 iOS News Notification")
        logger.info(f"Notification Data: {v5_data}")
        logger.info(f"Topics: {ios_topics}")
        try:
            ios_result = self.fcm.notify(
                data_payload=v5_data,
                topic_condition=ios_topics,
                notification_title=v5_data["title"],
                notification_body=v5_data["body"],
                fcm_options={"analytics_label": f"v5_ios_news_{v5_data['article_id']}"},
                apns_config={
                    "headers": {
                        "apns-priority": "10",
                        "apns-collapse-id": f"news_{v5_data['article_id']}",
                    },
                    "payload": {
                        "aps": {
                            "mutable-content": 1,
                        },
                    },
                },
                timeout=240,
            )
            logger.info(f"V5 iOS News Result: {ios_result}")
            record_send(platform="ios", category="news", success=True, result=ios_result)
        except Exception as e:
            logger.error(f"V5 iOS News Notification Error: {e}")
            record_send(platform="ios", category="news", success=False)
        logger.info("----------------------------------------------------------")

    def send_v3_notification(self, article, data):
        if not self.DEBUG:
            topics = "'prod_v3' in topics && 'featured_news' in topics"
            flutter_topics = "'flutter_production_v3' in topics && 'featured_news' in topics"
        else:
            topics = "'debug_v3' in topics && 'featured_news' in topics"
            flutter_topics = "'flutter_debug_v3' in topics && 'featured_news' in topics"
        self.send_to_fcm(article, data, topics, flutter_topics)

    def send_to_fcm(self, article, data, topics, flutter_topics):
        logger.info("----------------------------------------------------------")
        logger.info(f"Sending News notification - {article.title}")
        news_info = json.loads(data["item"])
        try:
            logger.info(f"News Notification Data - {data}")
            logger.info(f"Topics - {topics}")
            android_result = self.fcm.notify(
                notification_title="New article via " + news_info["news_site_long"],
                notification_body=news_info["title"],
                topic_condition=topics,
            )
            logger.info(android_result)
        except Exception as e:
            logger.error(e)

        logger.info("----------------------------------------------------------")

        logger.info("----------------------------------------------------------")
        logger.info(f"Sending News Flutter notification - {article.title}")
        try:
            logger.info(f"News Notification Data - {data}")
            logger.info(f"Topics - {flutter_topics}")

            flutter_results = self.fcm.notify(
                data_payload=data,
                topic_condition=flutter_topics,
                notification_title="New article via " + news_info["news_site_long"],
                notification_body=news_info["title"],
            )
            logger.info(flutter_results)
        except Exception as e:
            logger.error(e)

        logger.info("----------------------------------------------------------")
