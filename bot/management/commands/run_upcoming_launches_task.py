from django.core.management import BaseCommand
from bot.tasks import get_upcoming_launches
from celery.utils.log import get_task_logger

logger = get_task_logger('bot')

TAG = 'Digest Server'


class Command(BaseCommand):
    help = 'Run Get Upcoming Launches manually.'

    def handle(self, *args, **options):
        logger.info('Get Upcoming Launches')
        get_upcoming_launches()
