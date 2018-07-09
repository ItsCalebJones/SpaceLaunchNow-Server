import requests
from api.models import *
from django.core.management import BaseCommand

from api.utils.utilities import get_agency_type


def get_agency_data():
    Agency.objects.all().delete()
    results = requests.get("http://launchlibrary.net/1.3/agency?limit=1000")
    agencies = results.json()['agencies']
    for data in agencies:
        agency, created = Agency.objects.get_or_create(id=data['id'])
        agency.name = data['name']
        agency.country_code = data['countryCode']
        agency.abbrev = data['abbrev']
        agency.type = get_agency_type(data['type'])
        try:
            if data['infoURLs'] is not None and len(data['infoURLs']) > 0:
                agency.info_url = data['infoURLs'][0]
        except KeyError:
            print agency.id
            print data
        try:
            agency.wiki_url = data['wikiURL']
        except KeyError:
            print agency.id
            print data
        agency.save()


def get_rocket_data():
    results = requests.get("http://launchlibrary.net/1.3/rocket?limit=1000&mode=verbose")
    rockets = results.json()['rockets']
    for data in rockets:
        rocket, created = Launcher.objects.get_or_create(id=data['id'])
        rocket.name = data['name']
        rocket.family = data['family']['name']
        rocket.variant = data['configuration']
        rocket.legacy_image_url = data['imageURL']
        try:
            if data['infoURLs'] is not None and len(data['infoURLs']) > 0:
                rocket.info_url = data['infoURLs'][0]
        except KeyError:
            print rocket.id
            print data
        try:
            rocket.wiki_url = data['wikiURL']
        except KeyError:
            print rocket.id
            print data
        rocket.save()


class Command(BaseCommand):
    help = 'Run import manually.'

    def handle(self, *args, **options):
        response = raw_input('Continue with importing from LL ? (Y/N) ')
        if response == "Y":
            get_agency_data()
            get_rocket_data()
