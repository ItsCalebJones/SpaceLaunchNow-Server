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
            print "Mission %s" % mission.id
            print mission.type


def update_agencies():
    agencies = Agency.objects.all()
    for agency in agencies:
        try:
            agency_type = AgencyType.objects.get(name=agency.type)
            agency.agency_type = agency_type
            agency.save()
        except ObjectDoesNotExist:
            print "Agency %s" % agency.id
            print agency.type


class Command(BaseCommand):
    help = 'Run import manually.'

    def handle(self, *args, **options):
        response = raw_input('Continue with importing Types from LL ? (Y/N) ')
        if response == "Y":
            get_agency_type()
            get_mission_type()
            update_missions()
            update_agencies()
