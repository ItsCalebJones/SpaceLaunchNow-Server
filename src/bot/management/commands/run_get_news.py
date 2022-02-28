from django.core.management import BaseCommand
from celery.utils.log import get_task_logger

from bot.app.sync.news_sync import get_news
from bot.app.sync.twitter_sync import get_new_tweets
from bot.app.sync.reddit_sync import get_submissions

logger = get_task_logger('bot.events')

TAG = 'Digest Server'


class Command(BaseCommand):
    help = 'Run get News manually.'

    def handle(self, *args, **options):
        logger.info('Check Events')
        get_news()
        get_new_tweets()
        get_submissions()
