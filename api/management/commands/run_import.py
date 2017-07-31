from django.core.management import BaseCommand
from celery.utils.log import get_task_logger
import api.utils.data_importer as importer

logger = get_task_logger('bot')

TAG = 'API'


class Command(BaseCommand):
    help = 'Run import manually.'

    def handle(self, *args, **options):
        logger.info('Running importer...')
        importer.main()
