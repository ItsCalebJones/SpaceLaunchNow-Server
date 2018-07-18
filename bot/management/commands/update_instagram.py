from django.core.management import BaseCommand
from celery.utils.log import get_task_logger

from bot.tasks import set_instagram

logger = get_task_logger('bot')

TAG = 'Instagram Bot'


class Command(BaseCommand):
    help = 'Update Instagram profile.'

    def handle(self, *args, **options):
        logger.info('Running Instagram update...')
        set_instagram()
