import requests
from celery.utils.log import get_task_logger

from api.models import *
from django.core.management import BaseCommand

logger = get_task_logger('bot')


class Command(BaseCommand):
    def handle(self, *args, **options):
        astroFlights = AstronautFlight.objects.all()
        requireMore = []

        for astroFlight in astroFlights:
            uses = 0
            uses = (astroFlight.launch_crew.all().count() +
                    astroFlight.onboard_crew.all().count() +
                    astroFlight.landing_crew.all().count() +
                    astroFlight.expeditions.all().count())

            if uses > 1:
                requireMore.append((astroFlight.id, uses))

        print(len(requireMore))

        for id, uses in requireMore:
            itemsCreated = []
            currentAstroFlight = AstronautFlight.objects.get(pk=id)
            numberToRemove = uses-1
            for i in range(0, numberToRemove):
                newItem = AstronautFlight()
                newItem.astronaut = currentAstroFlight.astronaut
                newItem.role = currentAstroFlight.role
                newItem.save()
                itemsCreated.append(newItem)
            try:
                print(currentAstroFlight.astronaut.name)
            except Exception:
                print("Error printing name.")

            while numberToRemove > 0:
                spacecraft_flight_launch_crew = SpacecraftFlight.objects.filter(launch_crew__id=id)
                for spacecraft_flight in spacecraft_flight_launch_crew:
                    if numberToRemove > 0:
                        numberToRemove = numberToRemove - 1
                        spacecraft_flight.launch_crew.remove(currentAstroFlight)
                        spacecraft_flight.launch_crew.add(itemsCreated[numberToRemove-1])

                spacecraft_flight_onboard_crew = SpacecraftFlight.objects.filter(onboard_crew__id=id)
                for spacecraft_flight in spacecraft_flight_onboard_crew:
                    if numberToRemove > 0:
                        numberToRemove = numberToRemove - 1
                        spacecraft_flight.onboard_crew.remove(currentAstroFlight)
                        spacecraft_flight.onboard_crew.add(itemsCreated[numberToRemove - 1])

                spacecraft_flight_landing_crew = SpacecraftFlight.objects.filter(landing_crew__id=id)
                for spacecraft_flight in spacecraft_flight_landing_crew:
                    if numberToRemove > 0:
                        numberToRemove = numberToRemove - 1
                        spacecraft_flight.landing_crew.remove(currentAstroFlight)
                        spacecraft_flight.landing_crew.add(itemsCreated[numberToRemove - 1])

                expeditions_crew = Expedition.objects.filter(crew__id=id)
                for expedition in expeditions_crew:
                    if numberToRemove > 0:
                        numberToRemove = numberToRemove - 1
                        expedition.crew.remove(currentAstroFlight)
                        expedition.crew.add(itemsCreated[numberToRemove-1])









