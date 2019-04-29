import logging

from pyfcm import FCMNotification

from bot.utils.config import keys
from spacelaunchnow import config

logger = logging.getLogger('bot.notifications')


class NewsNotificationHandler:

    def __init__(self, debug=None):
        if debug is None:
            self.DEBUG = config.DEBUG
        else:
            self.DEBUG = debug

    def send_notification(self, news):
        data = {"notification_type": 'featured_news',
                "item": {
                    "id": news.id,
                    "news_site_long": news.news_site,
                    "title": news.title,
                    "url": news.link,
                    "featured_image": news.featured_image
                }}

        if not self.DEBUG:
            topics = "'prod_v2' in topics && 'featured_news' in topics"
        else:
            topics = "'debug_v2' in topics && 'featured_news' in topics"

        logger.info('----------------------------------------------------------')
        logger.info('Sending News notification - %s' % news.title)
        push_service = FCMNotification(api_key=keys['FCM_KEY'])

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
