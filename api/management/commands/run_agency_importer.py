import requests
from api.models import *
from django.core.management import BaseCommand


def get_data():
    results = requests.get("http://launchlibrary.net/1.3/agency?limit=1000")
    agencies = results.json()['agencies']
    for agency in agencies:
        if Agency.objects.filter(name=agency['name']).exists():
            obj = Agency.objects.get(name=agency['name'])
            obj.launch_library_id = agency['id']
            obj.save()
            print ("Updated " + agency['name'])
        else:
            Agency.objects.create(name=agency['name'], launch_library_id=agency['id'])
            print ("Added " + agency['name'])


class Command(BaseCommand):
    help = 'Run import manually.'

    def handle(self, *args, **options):
        response = raw_input('Continue with importing from LL ? (Y/N) ')
        if response == "Y":
            get_data()
