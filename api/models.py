# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from django.contrib.sites.models import Site
from django.db.models import Q
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


class AgencyType(models.Model):
    id = models.IntegerField(primary_key=True, editable=True)
    name = models.CharField(max_length=255, blank=True, default="")

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name


class Agency(models.Model):
    id = models.IntegerField(primary_key=True, editable=True)
    name = models.CharField(max_length=200)
    parent = models.ForeignKey('self', related_name='related_agencies', null=True, blank=True)
    featured = models.BooleanField(default=False)
    country_code = models.CharField(max_length=255, blank=True, default="")
    abbrev = models.CharField(max_length=255, blank=True, default="")
    type = models.CharField(max_length=255, blank=True, null=True)
    agency_type = models.ForeignKey(AgencyType, related_name='agency', blank=True, null=True, on_delete=models.CASCADE)
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

    @property
    def successful_launches(self):
        count = Launch.objects.filter(lsp__id=self.id).filter(status=3).count()
        related_agency = self.related_agencies.all()
        for related in related_agency:
            count += Launch.objects.filter(lsp__id=related.id).count()
        return count

    @property
    def failed_launches(self):
        count = Launch.objects.filter(lsp__id=self.id).filter(Q(status=4) | Q(status=7)).count()
        related_agency = self.related_agencies.all()
        for related in related_agency:
            count += Launch.objects.filter(lsp__id=related.id).filter(Q(status=4) | Q(status=7)).count()
        return count

    @property
    def pending_launches(self):
        count = Launch.objects.filter(lsp__id=self.id).filter(Q(status=1) | Q(status=2) | Q(status=5)).count()
        related_agency = self.related_agencies.all()
        for related in related_agency:
            count += Launch.objects.filter(lsp__id=related.id).filter(Q(status=1) | Q(status=2) | Q(status=5)).count()
        return count

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
            return "https://launchlibrary.net/1.4/agency/%s" % self.id
        else:
            return None


# The Orbiter object is meant to define spacecraft (past and present) that are human-rated for spaceflight.
#
# Example: Dragon, Orion, etc.
class Orbiter(models.Model):
    id = models.IntegerField(primary_key=True, editable=True)
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
        verbose_name = 'Spacecraft'
        verbose_name_plural = 'Spacecrafts'


# The LauncherDetail object is meant to define orbital class launch vehicles (past and present).
#
# Example: Falcon 9, Saturn V, etc.
# TODO Deprecate the 'agency' string field now that its linked to launch_agency.
class LauncherConfig(models.Model):
    id = models.IntegerField(primary_key=True, editable=True)
    name = models.CharField(max_length=200)
    active = models.BooleanField(default=True)
    reusable = models.BooleanField(default=False)
    audited = models.BooleanField(default=False)
    librarian_notes = models.CharField(max_length=2048, default='', blank=True)
    description = models.CharField(max_length=2048, default='', blank=True)
    family = models.CharField(max_length=200, default='', blank=True)
    full_name = models.CharField(max_length=200, default='', blank=True)
    launch_agency = models.ForeignKey(Agency, related_name='launcher_list', blank=True, null=True)
    variant = models.CharField(max_length=200, default='', blank=True)
    alias = models.CharField(max_length=200, default='', blank=True)
    launch_cost = models.CharField(max_length=200, null=True, blank=True)
    min_stage = models.IntegerField(blank=True, null=True)
    max_stage = models.IntegerField(blank=True, null=True)
    length = models.FloatField(blank=True, null=True)
    diameter = models.FloatField(blank=True, null=True)
    launch_mass = models.IntegerField(blank=True, null=True)
    leo_capacity = models.IntegerField(blank=True, null=True)
    gto_capacity = models.IntegerField(blank=True, null=True)
    geo_capacity = models.IntegerField(blank=True, null=True)
    sso_capacity = models.IntegerField(blank=True, null=True)
    to_thrust = models.IntegerField(blank=True, null=True)
    apogee = models.IntegerField(blank=True, null=True)
    vehicle_range = models.IntegerField(blank=True, null=True)
    info_url = models.CharField(max_length=200, default='', blank=True, null=True)
    wiki_url = models.CharField(max_length=200, default='', blank=True, null=True)
    legacy_image_url = models.CharField(max_length=200, default='', blank=True)
    image_url = models.FileField(default=None, storage=LauncherImageStorage(), upload_to=image_path, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name

    def __unicode__(self):
        return u'%s' % self.full_name

    class Meta:
        ordering = ['name']
        verbose_name = 'Launcher Configurations'
        verbose_name_plural = 'Launcher Configurations'


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
    id = models.IntegerField(primary_key=True, editable=True)
    name = models.CharField(max_length=255, blank=True, default="")
    country_code = models.CharField(max_length=255, blank=True, default="")

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = 'Location'
        verbose_name_plural = 'Locations'


class Pad(models.Model):
    id = models.IntegerField(primary_key=True, editable=True)
    agency_id = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, default="")
    info_url = models.URLField(blank=True, null=True)
    wiki_url = models.URLField(blank=True, null=True)
    map_url = models.URLField(blank=True, null=True)
    latitude = models.CharField(blank=True, null=True, max_length=30)
    longitude = models.CharField(blank=True, null=True, max_length=30)
    location = models.ForeignKey(Location, related_name='pad', blank=True, on_delete=models.CASCADE)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = 'Pad'
        verbose_name_plural = 'Pads'


class Orbit(models.Model):
    name = models.CharField(primary_key=True, editable=True, max_length=30)
    abbrev = models.CharField(max_length=30)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name', ]
        verbose_name = 'Orbit'
        verbose_name_plural = 'Orbits'


class MissionType(models.Model):
    id = models.IntegerField(primary_key=True, editable=True)
    name = models.CharField(max_length=255, blank=True, default="")

    def __unicode__(self):
        return self.name


class Mission(models.Model):
    id = models.IntegerField(primary_key=True, editable=True)
    name = models.CharField(max_length=255, blank=True, default="")
    description = models.CharField(max_length=2048, blank=True, default="")
    type = models.IntegerField(blank=True, null=True)
    type_name = models.CharField(max_length=255, blank=True, default="")
    mission_type = models.ForeignKey(MissionType, related_name='mission', blank=True, null=True, on_delete=models.CASCADE)
    orbit = models.ForeignKey(Orbit, related_name='mission', null=True, blank=True, on_delete=models.CASCADE)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = 'Mission'
        verbose_name_plural = 'Missions'


class Payload(models.Model):
    id = models.IntegerField(primary_key=True, editable=True)
    name = models.CharField(max_length=255, blank=True, default="")
    description = models.CharField(max_length=2048, blank=True, default="")
    weight = models.CharField(max_length=255, blank=True, null=True)
    dimensions = models.CharField(max_length=255, blank=True, null=True)
    type = models.IntegerField(blank=True, null=True)
    total = models.IntegerField(blank=True, null=True)
    type_name = models.CharField(max_length=255, blank=True, default="")
    mission = models.ForeignKey(Mission, related_name='payloads', blank=True, null=True, on_delete=models.CASCADE)


class Launcher(models.Model):
    id = models.AutoField(primary_key=True)
    serial_number = models.CharField(max_length=10, blank=True, null=True)
    launcher_config = models.ForeignKey(LauncherConfig, related_name='launcher', null=True, on_delete=models.CASCADE)

    @property
    def previous_flights(self):
        count = Launch.objects.filter(launcher__id=self.id).filter(land_success=True).count()
        return count

    def __str__(self):
        return '%s (%s)' % (self.serial_number, self.launcher_config.full_name)

    def __unicode__(self):
        return u'%s (%s)' % (self.serial_number, self.launcher_config.full_name)

    class Meta:
        ordering = ['serial_number', ]
        verbose_name = 'Launcher'
        verbose_name_plural = 'Launchers'


class LaunchStatus(models.Model):
    id = models.IntegerField(primary_key=True, editable=True)
    name = models.CharField(max_length=255, blank=True, default="")

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = 'Launch Status'
        verbose_name_plural = 'Launch Statuses'


class Launch(models.Model):
    id = models.IntegerField(primary_key=True, editable=True)
    launch_library = models.NullBooleanField(default=True)
    name = models.CharField(max_length=255, blank=True)
    img_url = models.CharField(max_length=255, blank=True, null=True)
    status = models.IntegerField(blank=True, null=True)
    status_name = models.CharField(max_length=255, blank=True, null=True)
    launch_status = models.ForeignKey(LaunchStatus, related_name='launch', blank=True, null=True, on_delete=models.CASCADE)
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
    reused = models.BooleanField(default=False)
    land_success = models.NullBooleanField(blank=True, null=True)
    landing_type = models.CharField(max_length=10, blank=True, null=True)
    landing_location = models.CharField(max_length=10, blank=True, null=True)
    slug = models.SlugField(unique=True)
    lsp = models.ForeignKey(Agency, related_name='launch', null=True, on_delete=models.CASCADE)
    launcher = models.ManyToManyField(Launcher, related_name='launch')
    launcher_config = models.ForeignKey(LauncherConfig, related_name='launch', null=True, on_delete=models.CASCADE)
    pad = models.ForeignKey(Pad, related_name='launch', null=True, on_delete=models.CASCADE)
    mission = models.ForeignKey(Mission, related_name='launch', null=True, on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name + "-" + str(self.id))
        super(Launch, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return self.slug

    def get_full_absolute_url(self):
        return 'https://spacelaunchnow.me/launch/%s' % (self.get_absolute_url())

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
