import requests
from celery.utils.log import get_task_logger

from api.models import *
from django.core.management import BaseCommand

logger = get_task_logger('bot')


def import_core():
    results = requests.get("https://api.spacexdata.com/v2/parts/cores")
    types = results.json()
    for data in types:
        launcher, created = Launcher.objects.get_or_create(serial_number=data['core_serial'])
        if created:
            logger.info('Created new core %s', data['core_serial'])
            launcher.serial_number = data['core_serial']
            launcher.status = data['status']
            if data['details'] is not None:
                launcher.details = data['details']
            else:
                launcher.details = ""
            if data['rtls_landings'] > 0 or data['asds_landings']:
                launcher.flight_proven = True

            if data['block'] is 1:
                config = LauncherConfig.objects.get(id=90)
                launcher.launcher_config = config
            elif data['block'] is 2:
                config = LauncherConfig.objects.get(id=1)
                launcher.launcher_config = config
            elif data['block'] is 3:
                config = LauncherConfig.objects.get(id=80)
                launcher.launcher_config = config
            elif data['block'] is 4:
                config = LauncherConfig.objects.get(id=187)
                launcher.launcher_config = config
            elif data['block'] is 5:
                config = LauncherConfig.objects.get(id=188)
                launcher.launcher_config = config
        else:
            launcher.status = data['status']
            if data['details'] is not None:
                launcher.details = data['details']
        launcher.save()


class Command(BaseCommand):
    help = 'Run import manually.'

    def handle(self, *args, **options):
        response = input('Continue with importing SpaceX API? (Y/N) ')
        if response == "Y":
            import_core()
