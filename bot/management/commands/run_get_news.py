import datetime

import pytz
from django.core.management import BaseCommand
from celery.utils.log import get_task_logger

from api.models import Events
from bot.app.events.notification_handler import EventNotificationHandler
from bot.app.events.social_handler import SocialHandler
from bot.cogs.news import get_news

logger = get_task_logger('bot.events')

TAG = 'Digest Server'


class Command(BaseCommand):
    help = 'Run get News manually.'

    def handle(self, *args, **options):
        logger.info('Check Events')
        get_news()
