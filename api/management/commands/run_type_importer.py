import requests
from django.core.exceptions import ObjectDoesNotExist

from api.models import *
from django.core.management import BaseCommand

from api.utils.utilities import get_agency_type


def get_agency_type():
    results = requests.get("https://launchlibrary.net/1.4/agencytype")
    types = results.json()['types']
    for data in types:
        agency_types, created = AgencyType.objects.get_or_create(id=data['id'])
        agency_types.name = data['name']
        agency_types.save()


def get_launch_status():
    results = requests.get("https://launchlibrary.net/1.4/launchstatus")
    types = results.json()['types']
    for data in types:
        status, created = LaunchStatus.objects.get_or_create(id=data['id'])
        status.name = data['name']
        status.save()


def get_mission_type():
    results = requests.get("https://launchlibrary.net/1.4/missiontype")
    types = results.json()['types']
    for data in types:
        agency_types, created = MissionType.objects.get_or_create(id=data['id'])
        agency_types.name = data['name']
        agency_types.save()


def update_missions():
    missions = Mission.objects.all()
    for mission in missions:
        try:
            mission_type = MissionType.objects.get(id=mission.type)
            mission.mission_type = mission_type
            mission.save()
        except ObjectDoesNotExist:
            print("Mission %s" % mission.id)
            print(mission.type)


def update_agencies():
    agencies = Agency.objects.all()
    for agency in agencies:
        try:
            agency_type = AgencyType.objects.get(name=agency.type)
            agency.agency_type = agency_type
            agency.save()
        except ObjectDoesNotExist:
            print("Agency %s" % agency.id)
            print(agency.type)


def update_launches():
    launches = Launch.objects.all()
    for launch in launches:
        try:
            status = LaunchStatus.objects.get(name=launch.status)
            launch.status = status
            launch.save()
        except ObjectDoesNotExist:
            print("LaunchStatus %s" % launch.status)
            print(launch)


def import_core():
    results = requests.get("https://api.spacexdata.com/v2/parts/cores")
    types = results.json()
    for data in types:
        launcher, created = Launcher.objects.get_or_create(serial_number=data['core_serial'])
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
        launcher.save()


class Command(BaseCommand):
    help = 'Run import manually.'

    def handle(self, *args, **options):
        response = input('Continue with importing Types from LL ? (Y/N) ')
        if response == "Y":
            get_agency_type()
            get_mission_type()
            get_launch_status()
            update_missions()
            update_agencies()
            import_core()
