from django.core.management import BaseCommand
from celery.utils.log import get_task_logger

from bot.models import Launch

logger = get_task_logger('bot')


class Command(BaseCommand):
    help = 'Delete Notification and Launches'

    def handle(self, *args, **options):
        logger.info('Removing all launches and notifications.')
        Launch.objects.all().delete()
