from django.core.management import BaseCommand
from celery.utils.log import get_task_logger

from bot.app.Notifications import NotificationServer

logger = get_task_logger('bot')

TAG = 'Notification Server'


class Command(BaseCommand):
    help = 'Run Notifications manually.'

    def add_arguments(self, parser):
        parser.add_argument('-version', dest="version", type=str)
        parser.add_argument('-debug', dest="debug", type=bool)

    def handle(self, *args, **options):
        logger.info('Running Notifications...')
        debug = options['debug']
        version = options['version']
        notification = NotificationServer(debug=debug, version=version)
        notification.check_next_launch()
