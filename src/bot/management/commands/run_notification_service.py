import time

from django.core.management import BaseCommand
from celery.utils.log import get_task_logger


logger = get_task_logger('bot')

TAG = 'Notification Service'


def run():
    logger.info("Starting health check...")
    while True:
        logger.info("Health check!")


class Command(BaseCommand):
    help = 'Runs the notification service.'

    def handle(self, *args, **options):
        run()
        time.sleep(5)