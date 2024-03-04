import logging

from pyfcm import FCMNotification

from spacelaunchnow import settings

logger = logging.getLogger(__name__)


class NewsNotificationHandler:
    def __init__(self, debug=settings.DEBUG):
        self.DEBUG = debug
        self.api_key = settings.FCM_KEY

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
        push_service = FCMNotification(api_key=self.api_key)

        logger.info("----------------------------------------------------------")
        logger.info("Sending News notification - %s" % article.title)
        try:
            logger.info("News Notification Data - %s" % data)
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

        logger.info("----------------------------------------------------------")
        logger.info("Sending News Flutter notification - %s" % article.title)
        try:
            logger.info("News Notification Data - %s" % data)
            logger.info("Topics - %s" % flutter_topics)
            flutter_results = push_service.notify_topic_subscribers(
                data_message=data,
                condition=flutter_topics,
                time_to_live=86400,
                message_title="New article via " + data["item"]["news_site_long"],
                message_body=data["item"]["title"],
            )
            logger.info(flutter_results)
        except Exception as e:
            logger.error(e)

        logger.info("----------------------------------------------------------")
