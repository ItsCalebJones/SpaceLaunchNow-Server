import datetime

import pytz
from django.core.management import BaseCommand
from celery.utils.log import get_task_logger

from api.models import Events
from bot.app.events.twitter_handler import EventTwitterHandler

logger = get_task_logger('bot')

TAG = 'Digest Server'


class Command(BaseCommand):
    help = 'Run send Event manually.'

    def add_arguments(self, parser):
        parser.add_argument('-debug', dest="debug", type=bool, const=True, nargs='?')

    def handle(self, *args, **options):
        logger.info('Check Events')
        # event = Events.objects.filter(date__gte=datetime.datetime.now(tz=pytz.utc)).first()
        # if event:
        #     twitter = EventTwitterHandler()
        #     twitter.send_ten_minute_tweet(event)
