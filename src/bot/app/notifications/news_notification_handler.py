import json
import logging

from bot.app.notification_service import NotificationService

logger = logging.getLogger(__name__)


class NewsNotificationHandler(NotificationService):
    def send_notification(self, article):
        data = {
            "notification_type": "featured_news",
            "click_action": "FLUTTER_NOTIFICATION_CLICK",
            "item": {
                "id": None,
                "article_id": article.id,
                "news_site_long": article.news_site,
                "newsSite": article.news_site,
                "title": article.title,
                "url": article.link,
                "featured_image": article.featured_image,
                "imageUrl": article.featured_image,
            },
        }
        data["item"] = json.dumps(data["item"])
        self.send_v3_notification(article, data)

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
