import json

from django.core.management import BaseCommand
from celery.utils.log import get_task_logger
import api.utils.data_importer as importer
from api.models import Launcher, Orbiter, Agency

logger = get_task_logger('bot')

TAG = 'API'


class Command(BaseCommand):
    help = 'Run import manually.'

    def handle(self, *args, **options):
        logger.info('Running importer...')
        with open('launchers.json') as my_file:
            data = json.load(my_file)
        for launcher_data in data['results']:
            name = launcher_data['name']
            result = Launcher.objects.filter(name__contains=name)
            for launcher in result:
                if launcher_data['full_name'] in launcher.name:
                    agency = Agency.objects.filter(name__contains=launcher_data['agency'])
                    if len(agency) > 0:
                        launcher.launch_agency = agency[0]
                    else:
                        agency = Agency.objects.filter(abbrev__contains=launcher_data['agency'])
                        if len(agency) > 0:
                            launcher.launch_agency = agency[0]
                    launcher.description = launcher_data['description']
                    launcher.family = launcher_data['family']
                    launcher.agency = launcher_data['agency']
                    launcher.full_name = launcher_data['full_name']
                    launcher.variant = launcher_data['variant']
                    launcher.alias = launcher_data['alias']
                    launcher.min_stage = launcher_data['min_stage']
                    launcher.max_stage = launcher_data['max_stage']
                    launcher.length = launcher_data['length']
                    launcher.diameter = launcher_data['diameter']
                    launcher.launch_mass = launcher_data['launch_mass']
                    launcher.leo_capacity = launcher_data['leo_capacity']
                    launcher.gto_capacity = launcher_data['gto_capacity']
                    launcher.to_thrust = launcher_data['to_thrust']
                    launcher.apogee = launcher_data['apogee']
                    launcher.vehicle_range = launcher_data['vehicle_range']
                    launcher.image_url = launcher_data['image_url']
                    launcher.info_url = launcher_data['info_url']
                    launcher.wiki_url = launcher_data['wiki_url']
                    launcher.save()
