import json
import os
import tempfile
from django.core import files

import requests
from django.core.management import BaseCommand

from api.models import Launcher


class Command(BaseCommand):
    help = 'Run import manually.'

    def handle(self, *args, **options):
        for each in Launcher.objects.all():
            if each.image_url == '':
                result = requests.get("http://launchlibrary.net/1.3/rocket/" + str(each.id))
                webrocket = result.json()['rockets'][0]

                if 'placeholder' not in webrocket['imageURL']:
                    request = requests.get(webrocket['imageURL'], stream=True)
                    file_name = webrocket['imageURL'].split('/')[-1]
                    os.rename(file_name, each.id)
                    lf = tempfile.NamedTemporaryFile()

                    for block in request.iter_content(1024*8):
                        if not block:
                            break
                        lf.write(block)

                    imageFile = Launcher.objects.get(id=each.id).image_url
                    imageFile.save(file_name, files.File(lf))

                    print(each.name)

