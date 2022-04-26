import logging

import time

from django.core.management import BaseCommand

logger = logging.getLogger(__name__)

TAG = 'Notification Service'


def run():
    logger.info("Starting health check...")
    while True:
        logger.info("Health check!")
        time.sleep(30)


class Command(BaseCommand):
    help = 'Runs the notification service.'

    def handle(self, *args, **options):
        run()
