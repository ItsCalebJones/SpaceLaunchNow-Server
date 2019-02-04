import sys

from PIL import Image
from compat import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile


def get_launch_status(status):
    switcher = {
        0: 'Unknown',
        1: 'Go for Launch',
        2: 'Launch is NO-GO',
        3: 'Successful Launch',
        4: 'Launch Failed',
        5: 'Unplanned Hold',
        6: 'In Flight',
        7: 'Partial Failure',
    }
    return switcher.get(status, "Unknown")


def get_agency_type(agency_type):
    switcher = {
        0: 'Unknown',
        1: 'Government',
        2: 'Multinational',
        3: 'Commercial',
        4: 'Educational',
        5: 'Private',
        6: 'Unknown',
    }
    return switcher.get(agency_type, "Unknown")


def get_mission_type(mission_type):
    switcher = {
        0: 'Unknown',
        1: 'Earth Science',
        2: 'Planetary Science',
        3: 'Astrophysics',
        4: 'Heliophysics',
        5: 'Human Exploration',
        6: 'Robotic Exploration',
        7: 'Government/Top Secret',
        8: 'Tourism',
        9: 'Unknown',
        10: 'Communications',
        11: 'Resupply',
        12: 'Suborbital',
        13: 'Test Flight',
        14: 'Dedicated Rideshare',
        15: 'Navigation',
    }
    return switcher.get(mission_type, "Unknown")


def resize_for_upload(item):
    if item and hasattr(item, 'url'):
        try:
            basewidth = 1920
            image = Image.open(item)
            wpercent = (basewidth / float(image.size[0]))
            hsize = int((float(image.size[1]) * float(wpercent)))

            output = BytesIO()
            image = image.resize((basewidth, hsize), Image.ANTIALIAS)

            if image.format == 'PNG' or image.mode == 'RGBA' or 'png' in item.name:
                imageformat = 'PNG'
            else:
                imageformat = 'JPEG'

            image.save(output, format=imageformat, optimize=True)
            output.seek(0)

            return InMemoryUploadedFile(output, 'FileField',
                                        ("%s." + imageformat.lower()) % item.name.split('.')[0],
                                        'image/' + imageformat.lower(),
                                        sys.getsizeof(output), None)
        except:
            return item
    else:
        return item
