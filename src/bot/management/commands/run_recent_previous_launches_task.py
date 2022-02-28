from django.core.management import BaseCommand
from bot.tasks import get_recent_previous_launches
from celery.utils.log import get_task_logger

logger = get_task_logger('bot')

TAG = 'Digest Server'


class Command(BaseCommand):
    help = 'Run Get Recent Previous Launches manually.'

    def handle(self, *args, **options):
        logger.info('Get Recent Previous Launches')
        get_recent_previous_launches()
