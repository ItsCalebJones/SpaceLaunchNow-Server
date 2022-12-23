import os

import django
from api.models import Astronaut
from configurations.models import AstronautStatus

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "spacelaunchnow.settings")
django.setup()


if __name__ == "__main__":
    deceased, created = AstronautStatus.objects.get_or_create(name="Deceased")
    retired = AstronautStatus.objects.get(name="Retired")
    retired_with_death_date = Astronaut.objects.filter(status=retired).filter(date_of_death__isnull=False)
    for astronaut in retired_with_death_date:
        print("--------------------------------")
        print(astronaut)
        print(astronaut.status)
        print(astronaut.date_of_death)
        print("Migrating...")
        astronaut.status = deceased
        astronaut.save()
        print(astronaut)
        print(astronaut.status)
        print(astronaut.date_of_death)
        print("--------------------------------")
        print("/n")
