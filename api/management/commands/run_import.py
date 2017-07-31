from django.core.management import BaseCommand
from celery.utils.log import get_task_logger
import api.utils.data_importer as importer
from api.models import Launcher, Orbiter, LauncherDetail

logger = get_task_logger('bot')

TAG = 'API'


class Command(BaseCommand):
    help = 'Run import manually.'

    def handle(self, *args, **options):
        logger.info('Running importer...')
        response = raw_input('Delete all existing objects? (Y/N) ')
        if response == "Y":
            Launcher.objects.all().delete()
            Orbiter.objects.all().delete()
            LauncherDetail.objects.all().delete()
        response = raw_input('Continue with importing from http://calebjones.me/app ? (Y/N) ')
        if response == "Y":
            importer.main()
