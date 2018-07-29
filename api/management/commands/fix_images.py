import datetime
import os
import tempfile
import urllib

from django.core import files

import requests
from django.core.management import BaseCommand

from api.models import Launcher


class Command(BaseCommand):
    help = 'Run import manually.'

    def handle(self, *args, **options):
        for each in Launcher.objects.all():
            print("-------------")
            print(each)
            if each.image_url is None or each.image_url == '':
                each.image_url = ''
            else:
                print(each.image_url)
                print(each.image_url.url)
                if 'cloudinary' in each.image_url.url or 'imgur' in each.image_url.url:
                    print("Removing errored image.")
                    each.image_url = ''
            if each.image_url == '':
                each.save()
                result = requests.get("http://launchlibrary.net/1.3/rocket/" + str(each.id))
                if len(result.json()['rockets']) > 0:
                    webrocket = result.json()['rockets'][0]

                    if 'placeholder' not in webrocket['imageURL']:
                        request = requests.get(webrocket['imageURL'], stream=True)
                        filename = webrocket['imageURL'].split('/')[-1]
                        filename, file_extension = os.path.splitext(filename)
                        clean_name = urllib.quote(urllib.quote(each.name.encode('utf8')), '')
                        clean_name = "%s_nation_%s" % (
                        clean_name.lower(), datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
                        name = "%s%s" % (str(clean_name), file_extension)

                        lf = tempfile.NamedTemporaryFile()

                        for block in request.iter_content(1024 * 8):
                            if not block:
                                break
                            lf.write(block)

                        imageFile = Launcher.objects.get(id=each.id).image_url
                        imageFile.save(name, files.File(lf))

                        print(each.name)
            print("-------------")
