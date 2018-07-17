# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from django.contrib.sites.models import Site
from django.db.models.functions import datetime
from django.db import models
from custom_storages import LogoStorage, AgencyImageStorage, OrbiterImageStorage, LauncherImageStorage, \
    AgencyNationStorage, EventImageStorage

# The Agency object is meant to define a agency that operates launchers and orbiters.
#
# Example: SpaceX has Falcon 9 Launchers and Dragon orbiters
#
from django.template.defaultfilters import truncatechars, slugify
import urllib


def image_path(instance, filename):
    filename, file_extension = os.path.splitext(filename)
    clean_name = urllib.quote(urllib.quote(instance.name.encode('utf8')), '')
    clean_name = "%s_image_%s" % (clean_name.lower(), datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    name = "%s%s" % (str(clean_name), file_extension)
    return name


def nation_path(instance, filename):
    filename, file_extension = os.path.splitext(filename)
    clean_name = urllib.quote(urllib.quote(instance.name.encode('utf8')), '')
    clean_name = "%s_nation_%s" % (clean_name.lower(), datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    name = "%s%s" % (str(clean_name), file_extension)
    return name


def logo_path(instance, filename):
    filename, file_extension = os.path.splitext(filename)
    clean_name = urllib.quote(urllib.quote(instance.name.encode('utf8')), '')
    clean_name = "%s_logo_%s" % (clean_name.lower(), datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    name = "%s%s" % (str(clean_name), file_extension)
    return name


class Agency(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200)
    featured = models.BooleanField(default=False)
    country_code = models.CharField(max_length=255, blank=True, default="")
    abbrev = models.CharField(max_length=255, blank=True, default="")
    type = models.CharField(max_length=255, blank=True, null=True)
    info_url = models.URLField(blank=True, null=True)
    wiki_url = models.URLField(blank=True, null=True)
    description = models.CharField(max_length=2048, blank=True, null=True, default=None)
    launchers = models.CharField(max_length=500, default='', blank=True)
    orbiters = models.CharField(max_length=500, default='', blank=True)
    administrator = models.CharField(max_length=200, blank=True, null=True, default=None)
    founding_year = models.CharField(blank=True, null=True, default=None, max_length=20)
    legacy_image_url = models.URLField(blank=True, null=True, default=None)
    legacy_nation_url = models.URLField(blank=True, null=True, default=None)
    image_url = models.FileField(default=None, storage=AgencyImageStorage(), upload_to=image_path, null=True,
                                 blank=True)
    logo_url = models.FileField(default=None, storage=LogoStorage(), upload_to=logo_path, null=True, blank=True)
    nation_url = models.FileField(default=None, storage=AgencyNationStorage(), upload_to=nation_path, null=True,
                                  blank=True)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        ordering = ['name', 'featured', ]
        verbose_name = 'Agency'
        verbose_name_plural = 'Agencies'

    @property
    def short_description(self):
        return truncatechars(self.description, 50)

    @property
    def short_name(self):
        return truncatechars(self.name, 25)

    @property
    def launch_library_url(self):
        if self.id:
            return "https://launchlibrary.net/1.3/agency/%s" % self.id
        else:
            return None


# The Orbiter object is meant to define spacecraft (past and present) that are human-rated for spaceflight.
#
# Example: Dragon, Orion, etc.
class Orbiter(models.Model):
    name = models.CharField(max_length=200)
    agency = models.CharField(max_length=200, default='Unknown')
    launch_agency = models.ForeignKey(Agency, related_name='orbiter_list', blank=True, null=True)
    history = models.CharField(max_length=1000, default='')
    details = models.CharField(max_length=1000, default='')
    in_use = models.BooleanField(default=True)
    capability = models.CharField(max_length=2048, default='')
    wiki_link = models.URLField(blank=True)
    legacy_image_url = models.URLField(blank=True)
    legacy_nation_url = models.URLField(blank=True)
    image_url = models.FileField(default=None, storage=OrbiterImageStorage(), upload_to=image_path, null=True,
                                 blank=True)
    nation_url = models.FileField(default=None, storage=AgencyNationStorage(), upload_to=image_path, null=True,
                                  blank=True)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        ordering = ['name']
        verbose_name = 'Orbiter'
        verbose_name_plural = 'Orbiters'


# The LauncherDetail object is meant to define orbital class launch vehicles (past and present).
#
# Example: Falcon 9, Saturn V, etc.
# TODO Deprecate the 'agency' string field now that its linked to launch_agency.
class Launcher(models.Model):
    name = models.CharField(max_length=200)
    active = models.BooleanField(default=True)
    in_use = models.BooleanField(default=True)
    description = models.CharField(max_length=2048, default='', blank=True)
    family = models.CharField(max_length=200, default='', blank=True)
    agency = models.CharField(max_length=200, default='', blank=True)
    full_name = models.CharField(max_length=200, default='', blank=True)
    launch_agency = models.ForeignKey(Agency, related_name='launcher_list', blank=True, null=True)
    variant = models.CharField(max_length=200, default='', blank=True)
    alias = models.CharField(max_length=200, default='', blank=True)
    min_stage = models.IntegerField(blank=True, null=True)
    max_stage = models.IntegerField(blank=True, null=True)
    length = models.FloatField(blank=True, null=True)
    diameter = models.FloatField(blank=True, null=True)
    launch_mass = models.IntegerField(blank=True, null=True)
    leo_capacity = models.IntegerField(blank=True, null=True)
    gto_capacity = models.IntegerField(blank=True, null=True)
    to_thrust = models.IntegerField(blank=True, null=True)
    apogee = models.IntegerField(blank=True, null=True)
    vehicle_range = models.IntegerField(blank=True, null=True)
    capability = models.CharField(max_length=2048, default='', blank=True)
    info_url = models.CharField(max_length=200, default='', blank=True, null=True)
    wiki_url = models.CharField(max_length=200, default='', blank=True, null=True)
    legacy_image_url = models.CharField(max_length=200, default='', blank=True)
    image_url = models.FileField(default=None, storage=LauncherImageStorage(), upload_to=image_path, null=True,
                                 blank=True)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        ordering = ['name']
        verbose_name = 'Launcher Detail'
        verbose_name_plural = 'Launcher Details'


# The Events object is meant to define events (past and present).
# Example: Blue Origin Launches, ISS Crew returns, etc.
class Events(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=2048, default='', blank=True)
    location = models.CharField(max_length=100, default='', blank=True)
    feature_image = models.FileField(storage=EventImageStorage(), default=None, null=True, blank=True, upload_to=image_path)
    date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        ordering = ['name']
        verbose_name = 'Event'
        verbose_name_plural = 'Events'


class Location(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, default="")
    country_code = models.CharField(max_length=255, blank=True, default="")

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = 'Location'
        verbose_name_plural = 'Locations'


class Pad(models.Model):
    id = models.IntegerField(primary_key=True)
    agency_id = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, default="")
    info_url = models.URLField(blank=True, null=True)
    wiki_url = models.URLField(blank=True, null=True)
    map_url = models.URLField(blank=True, null=True)
    location = models.ForeignKey(Location, related_name='pad', blank=True, on_delete=models.CASCADE)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = 'Pad'
        verbose_name_plural = 'Pads'


class Mission(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, default="")
    description = models.CharField(max_length=2048, blank=True, default="")
    type = models.IntegerField(blank=True, null=True)
    type_name = models.CharField(max_length=255, blank=True, default="")

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = 'Mission'
        verbose_name_plural = 'Missions'


class Launch(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, blank=True)
    img_url = models.CharField(max_length=255, blank=True, null=True)
    status = models.IntegerField(blank=True, null=True)
    status_name = models.CharField(max_length=255,blank=True, null=True)
    netstamp = models.IntegerField(blank=True, null=True)
    wsstamp = models.IntegerField(blank=True, null=True)
    westamp = models.IntegerField(blank=True, null=True)
    net = models.DateTimeField(max_length=255, null=True)
    window_end = models.DateTimeField(max_length=255, null=True)
    window_start = models.DateTimeField(max_length=255, null=True)
    isostart = models.CharField(max_length=255, blank=True, null=True)
    isoend = models.CharField(max_length=255, blank=True, null=True)
    isonet = models.CharField(max_length=255, blank=True, null=True)
    inhold = models.NullBooleanField(default=False)
    tbdtime = models.NullBooleanField(default=False)
    tbddate = models.NullBooleanField(default=False)
    probability = models.IntegerField(blank=True, null=True)
    holdreason = models.CharField(max_length=255, blank=True, null=True)
    failreason = models.CharField(max_length=255, blank=True, null=True)
    hashtag = models.CharField(max_length=255, blank=True, null=True)
    slug = models.SlugField(unique=True)
    lsp = models.ForeignKey(Agency, related_name='launch', null=True, on_delete=models.CASCADE)
    launcher = models.ForeignKey(Launcher, related_name='launch', null=True, on_delete=models.CASCADE)
    pad = models.ForeignKey(Pad, related_name='launch', null=True, on_delete=models.CASCADE)
    mission = models.ForeignKey(Mission, related_name='launch', null=True, on_delete=models.CASCADE)

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name + "-" + str(self.id))
        super(Launch, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return self.slug

    def get_full_absolute_url(self):
        return 'https://spacelaunchnow.me/%s' % (self.get_absolute_url())

    class Meta:
        verbose_name = 'Launch'
        verbose_name_plural = 'Launches'


class VidURLs(models.Model):
    vid_url = models.URLField(max_length=200)
    launch = models.ForeignKey(Launch, related_name='vid_urls', on_delete=models.CASCADE)

    def __unicode__(self):
        return '%s' % self.vid_url

    class Meta:
        verbose_name = 'Video URL'
        verbose_name_plural = 'Video URLs'


class InfoURLs(models.Model):
    info_url = models.URLField(max_length=200)
    launch = models.ForeignKey(Launch, related_name='info_urls', on_delete=models.CASCADE)

    def __unicode__(self):
        return '%s' % self.info_url

    class Meta:
        verbose_name = 'Info URL'
        verbose_name_plural = 'Info URLs'
