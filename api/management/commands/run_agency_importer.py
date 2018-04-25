import requests
from api.models import *
from django.core.management import BaseCommand

def getDataEnter():
    results = requests.get("http://launchlibrary.net/1.3/agency?limit=1000")
    agencies = results.json()['agencies']
    for agency in agencies:
        print(agency['name'])
        Agency.objects.create(agency=agency['name'], description="", launch_library_id=agency['id'])


class Command(BaseCommand):
    help = 'Run import manually.'

    def handle(self, *args, **options):
        response = raw_input('Continue with importing from LL ? (Y/N) ')
        if response == "Y":
            getDataEnter()
