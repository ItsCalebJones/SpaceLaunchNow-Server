import logging

from pyfcm import FCMNotification

from bot.app.buffer import BufferAPI
from spacelaunchnow.config import keys
from spacelaunchnow import config

logger = logging.getLogger('bot.notifications')


class NewsNotificationHandler:

    def __init__(self, debug=None):
        if debug is None:
            self.DEBUG = config.DEBUG
        else:
            self.DEBUG = debug
        self.buffer = BufferAPI()

    def send_notification(self, article):
        data = {"notification_type": 'featured_news',
                "click_action": "FLUTTER_NOTIFICATION_CLICK",
                "item": {
                    "id": article.id,
                    "news_site_long": article.news_site,
                    "title": article.title,
                    "url": article.link,
                    "featured_image": article.featured_image
                }}
        self.send_v2_notification(article, data)
        self.send_v3_notification(article, data)

    def send_v3_notification(self, article, data):
        if not self.DEBUG:
            topics = "'prod_v3' in topics && 'featured_news' in topics"
            flutter_topics = "'flutter_production_v3' in topics && 'featured_news' in topics"
        else:
            topics = "'debug_v3' in topics && 'featured_news' in topics"
            flutter_topics = "'flutter_debug_v3' in topics && 'featured_news' in topics"
        self.send_to_fcm(article, data, topics, flutter_topics)

    def send_v2_notification(self, article, data):
        if not self.DEBUG:
            topics = "'prod_v2' in topics && 'featured_news' in topics"
            flutter_topics = "'flutter_production_v2' in topics && 'featured_news' in topics"
        else:
            topics = "'debug_v2' in topics && 'featured_news' in topics"
            flutter_topics = "'flutter_debug_v2' in topics && 'featured_news' in topics"
        self.send_to_fcm(article, data, topics, flutter_topics)

    def send_to_fcm(self, article, data, topics, flutter_topics):
        push_service = FCMNotification(api_key=keys['FCM_KEY'])

        logger.info('----------------------------------------------------------')
        logger.info('Sending News notification - %s' % article.title)
        try:
            logger.info('News Notification Data - %s' % data)
            logger.info('Topics - %s' % topics)
            android_result = push_service.notify_topic_subscribers(data_message=data,
                                                                   condition=topics,
                                                                   time_to_live=86400, )
            logger.info(android_result)
        except Exception as e:
            logger.error(e)

        logger.info('----------------------------------------------------------')

        logger.info('----------------------------------------------------------')
        logger.info('Sending News Flutter notification - %s' % article.title)
        try:
            logger.info('News Notification Data - %s' % data)
            logger.info('Topics - %s' % flutter_topics)
            flutter_results = push_service.notify_topic_subscribers(data_message=data,
                                                                    condition=flutter_topics,
                                                                    time_to_live=86400,
                                                                    message_title="New article via " + data['item'][
                                                                        'news_site_long'],
                                                                    message_body=data['item']['title']
                                                                    )
            logger.info(flutter_results)
        except Exception as e:
            logger.error(e)

        logger.info('----------------------------------------------------------')

    def send_to_social(self, article):
        logger.info('Sending News ID:%s to Buffer!', article.id)
        if article.link:
            logger.info(self.buffer.send_to_twitter(message=article.title, link=article.link, now=True))
            logger.info(self.buffer.send_to_facebook(message=article.title, link=article.link, now=True))
            logger.info('Sent to Buffer!')
