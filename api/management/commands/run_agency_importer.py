import requests
from api.models import *
from django.core.management import BaseCommand

def getDataEnter():
    results = requests.get("http://launchlibrary.net/1.3/agency?limit=1000")
    agencies = results.json()['agencies']
    for agency in agencies:
        if( Agency.objects.filter(agency=agency['name']).exists() ):
            agencyObj = Agency.objects.get(agency=agency['name'])
            agencyObj.launch_library_id = agency['id']
            agencyObj.save()
            print ("Updated " + agency['name'])
        else:
            Agency.objects.get_or_create(agency=agency['name'], launch_library_id=agency['id'])
            print ("Added " + agency['name'])


class Command(BaseCommand):
    help = 'Run import manually.'

    def handle(self, *args, **options):
        response = raw_input('Continue with importing from LL ? (Y/N) ')
        if response == "Y":
            getDataEnter()