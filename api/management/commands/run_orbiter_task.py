import json
from django.core.management import BaseCommand
from api.models import Orbiter, Agency


class Command(BaseCommand):
    help = 'Run import manually'

    def handle(self, *args, **options):
        print "Running importer..."
        with open('orbiters.json') as my_file:
            data = json.load(my_file)
            for orb in data['results']:
                if Orbiter.objects.filter(name=orb['name']).exists():
                    print "Exists" + orb['name']
                else:
                    if Agency.objects.filter(name=orb['agency']).exists():
                        agency = Agency.objects.get(name=orb['agency'])

                        Orbiter.objects.create(id=orb['id'], name=orb['name'], agency=orb['agency'],
                                               launch_agency=agency, history=orb['history'], details=orb['details'],
                                               image_url=orb['image_url'], legacy_nation_url=orb['legacy_nation_url'],
                                               nation_url=orb['nation_url'], wiki_link=orb['wiki_link'],
                                               in_use=orb['in_use'], capability=orb['capability'])
                        print "Added " + orb['name']

                    else:
                        print "Unable to find " + orb['agency'] + " in your DB"
