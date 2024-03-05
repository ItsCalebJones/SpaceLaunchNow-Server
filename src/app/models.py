import datetime
import os

try:
    from urllib import quote  # Python 2.X
except ImportError:
    from urllib.parse import quote  # Python 3+

from django.conf import settings
from django.core.files.storage import default_storage
from django.db import models
from storages.backends.s3boto3 import S3Boto3Storage

from custom_storages import AppImageStorage
from spacelaunchnow.base_models import SingletonModel


def image_path(instance, filename):
    filename, file_extension = os.path.splitext(filename)
    name = "%s%s" % ("navigation_drawer_default", file_extension)
    return name


def language_image_path(instance, filename):
    filename, file_extension = os.path.splitext(filename)
    clean_name = quote(quote(instance.name.encode("utf8")), "")
    clean_name = "%s_language_%s" % (clean_name.lower(), datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    name = "%s%s" % (str(clean_name), file_extension)
    return name


def profile_image_path(instance, filename):
    filename, file_extension = os.path.splitext(filename)
    clean_name = quote(quote(instance.name.encode("utf8")), "")
    clean_name = "%s_profile_%s" % (clean_name.lower(), datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    name = "%s%s" % (str(clean_name), file_extension)
    return name


def select_storage(storage: S3Boto3Storage = None):
    return default_storage if (settings.USE_LOCAL_STORAGE) else AppImageStorage()


class AppConfig(SingletonModel):
    navigation_drawer_image = models.FileField(
        storage=select_storage(storage=AppImageStorage), default=None, null=True, blank=True, upload_to=image_path
    )

    def __str__(self):
        return "Space Launch Now - Android App Config"

    def __unicode__(self):
        return "Space Launch Now - Android App Config"

    class Meta:
        verbose_name = "Android App Config"
        verbose_name_plural = "Android App Config"


class Nationality(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    flag = models.FileField(storage=select_storage, upload_to=language_image_path)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return "%s" % self.name

    class Meta:
        verbose_name = "Nationality"
        verbose_name_plural = "Nationalities"


class Translator(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    link = models.CharField(
        max_length=200,
        null=True,
        blank=True,
    )
    nationality = models.ForeignKey(
        Nationality, related_name="translator", null=True, blank=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return self.name

    def __unicode__(self):
        return "%s" % self.name

    class Meta:
        verbose_name = "Translator"
        verbose_name_plural = "Translators"


class Staff(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    title = models.CharField(
        max_length=200,
        null=True,
        blank=True,
    )
    bio = models.CharField(
        max_length=2048,
        null=True,
        blank=True,
    )
    link = models.CharField(
        max_length=200,
        null=True,
        blank=True,
    )
    profile = models.FileField(storage=select_storage, upload_to=profile_image_path)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return "%s" % self.name

    class Meta:
        verbose_name = "Staff"
        verbose_name_plural = "Staff"
