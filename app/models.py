import datetime
import os
try:
    from urllib import quote  # Python 2.X
except ImportError:
    from urllib.parse import quote  # Python 3+

from django.db import models

from custom_storages import AppImageStorage
from spacelaunchnow.base_models import SingletonModel


def image_path(instance, filename):
    filename, file_extension = os.path.splitext(filename)
    name = "%s%s" % ("navigation_drawer_default", file_extension)
    return name


class AppConfig(SingletonModel):
    navigation_drawer_image = models.FileField(storage=AppImageStorage(), default=None, null=True, blank=True,
                                               upload_to=image_path)

    def __str__(self):
        return "Space Launch Now - Android App Config"

    def __unicode__(self):
        return u"Space Launch Now - Android App Config"

    class Meta:
        verbose_name = 'Android App Config'
        verbose_name_plural = 'Android App Config'


class Translator(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
