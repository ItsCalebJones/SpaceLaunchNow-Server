import logging
import sys

from PIL import Image
from compat import BytesIO
from django.contrib.admin.options import BaseModelAdmin
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile

from spacelaunchnow import config


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


def resize_needed(item):
    if item and hasattr(item, 'url'):
        try:
            image = Image.open(item)
            if image.size[0] > 1920:
                return True
        except:
            return False
    return False


def resize_for_upload(item):
    if item and hasattr(item, 'url'):
        try:
            basewidth = 1920
            image = Image.open(item)
            if image.size[0] <= 1920:
                return item
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


def admin_change_url(obj):
    app_label = obj._meta.app_label
    model_name = obj._meta.model.__name__.lower()
    return reverse('admin:{}_{}_change'.format(
        app_label, model_name
    ), args=(obj.pk,))


def admin_link(attr, short_description, empty_description="-"):
    """Decorator used for rendering a link to a related model in
    the admin detail page.
    attr (str):
        Name of the related field.
    short_description (str):
        Name if the field.
    empty_description (str):
        Value to display if the related field is None.
    The wrapped method receives the related object and should
    return the link text.
    Usage:
        @admin_link('credit_card', _('Credit Card'))
        def credit_card_link(self, credit_card):
            return credit_card.name
    """

    def wrap(func):
        def field_func(self, obj):
            related_obj = getattr(obj, attr)
            if related_obj is None:
                return empty_description
            url = admin_change_url(related_obj)
            return format_html(
                '<a href="{}">{}</a>',
                url,
                func(self, related_obj)
            )

        field_func.short_description = short_description
        field_func.allow_tags = True
        return field_func

    return wrap


def get_map_url(location):
    import requests
    logger = logging.getLogger('django')
    # Enter your api key here
    api_key = config.GOOGLE_API_KEY

    # url variable store url
    url = "https://maps.googleapis.com/maps/api/staticmap?"

    # center defines the center of the map,
    # equidistant from all edges of the map.
    center = location.name

    # zoom defines the zoom
    # level of the map
    zoom = 8

    # get method of requests module
    # return response object
    full_url = (url + "center=" + center + "&zoom=" +
           str(zoom) + "&maptype=hybrid&size= 600x400&scale=2&key=" +
           api_key)
    logger.info(full_url)
    image_content = ContentFile(requests.get(full_url).content)
    location.map_image.save("temp.jpg", image_content)
    logger.info(location.map_image.url)


def get_pad_url(pad):
    import requests
    logger = logging.getLogger('django')
    # Enter your api key here
    api_key = config.GOOGLE_API_KEY

    # url variable store url
    url = "https://maps.googleapis.com/maps/api/staticmap?"

    # center defines the center of the map,
    # equidistant from all edges of the map.
    center = pad.latitude + "," + pad.longitude

    # zoom defines the zoom
    # level of the map
    zoom = 12

    # get method of requests module
    # return response object
    full_url = (url + "center=" + center + "&zoom=" +
           str(zoom) + "&maptype=hybrid&size= 600x400&scale=2" +
           "&markers=color:blue|label:P|" + pad.latitude + "," + pad.longitude + "&key=" +
           api_key)
    logger.info(full_url)
    image_content = ContentFile(requests.get(full_url).content)
    pad.map_image.save("temp.jpg", image_content)
    logger.info(pad.map_image.url)


class AdminBaseWithSelectRelated(BaseModelAdmin):
    """
    Admin Base using list_select_related for get_queryset related fields
    """
    list_select_related = []

    def get_queryset(self, request):
        return super(AdminBaseWithSelectRelated, self).get_queryset(request).select_related(*self.list_select_related)

    def form_apply_select_related(self, form):
        for related_field in self.list_select_related:
            splitted = related_field.split('__')

            if len(splitted) > 1:
                field = splitted[0]
                related = '__'.join(splitted[1:])
                form.base_fields[field].queryset = form.base_fields[field].queryset.select_related(related)
