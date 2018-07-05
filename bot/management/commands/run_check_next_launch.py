from django.core.management import BaseCommand
from bot.tasks import check_next_launch
from celery.utils.log import get_task_logger

logger = get_task_logger('bot')

TAG = 'Digest Server'


class Command(BaseCommand):
    help = 'Run Check Next Launch manually.'

    def handle(self, *args, **options):
        logger.info('Check Next Launch')
        check_next_launch()
