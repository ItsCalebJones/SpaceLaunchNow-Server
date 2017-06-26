from django.core.management import BaseCommand
from celery.utils.log import get_task_logger

logger = get_task_logger('bot')

TAG = 'Notification Server'


class Command(BaseCommand):
    help = 'Run Notifications manually.'

    def handle(self, *args, **options):
        logger.info('Running Notifications - ')


