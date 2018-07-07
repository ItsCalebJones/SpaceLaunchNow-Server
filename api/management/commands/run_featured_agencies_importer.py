import json
from django.core.management import BaseCommand
from api.models import Agency


class Command(BaseCommand):
    help = 'Run import manually'

    def handle(self, *args, **options):

        print "Running importer..."
        with open('agencies.json') as my_file:
            data = json.load(my_file)
            for ag in data['results']:
                if ag['featured']:

                    agencyName = ""

                    if ag['name'] == "JAXA":
                        agencyName = "Japan Aerospace Exploration Agency"
                    elif ag['name'] == "Khrunichev":
                        agencyName = "Khrunichev State Research and Production Space Center"
                    elif ag['name'] == "NASA":
                        agencyName = "National Aeronautics and Space Administration"
                    elif ag['name'] == "ROSCOSMOS":
                        agencyName = "Russian Federal Space Agency (ROSCOSMOS)"
                    elif ag['name'] == "Yuzhnoye":
                        agencyName = "Yuzhnoye Design Bureau"
                    else:
                        agencyName = ag['name']

                    if not Agency.objects.filter(name=agencyName).exists():
                        print agencyName + " not in agency list run agency importer first!"
                    else:
                        agency = Agency.objects.get(name=agencyName)
                        agency.name = agencyName
                        agency.featured = ag['featured']
                        agency.description = ag['description']
                        agency.launchers = ag['launchers']
                        agency.orbiters = ag['orbiters']
                        agency.ceo = ag['ceo']
                        agency.founding_year = ag['founding_year']
                        agency.legacy_image_url = ag['legacy_image_url']
                        agency.legacy_nation_url = ag['legacy_nation_url']
                        agency.image_url = ag['image_url']
                        agency.logo_url = ag['logo_url']
                        agency.nation_url = ag['nation_url']
                        agency.save()
                        print agencyName + " featured info added"
