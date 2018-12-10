# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import uuid

try:
    from urllib import quote  # Python 2.X
except ImportError:
    from urllib.parse import quote  # Python 3+

from django.core.cache import cache
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q, F
from django.db.models.functions import datetime
from django.db import models

from configurations.models import *
from custom_storages import LogoStorage, AgencyImageStorage, OrbiterImageStorage, LauncherImageStorage, \
    AgencyNationStorage, EventImageStorage, AstronautImageStorage

# The Agency object is meant to define a agency that operates launchers and spacecrafts.
#
# Example: SpaceX has Falcon 9 Launchers and Dragon spacecrafts
#
from django.template.defaultfilters import truncatechars, slugify
import urllib

CACHE_TIMEOUT_ONE_DAY = 24 * 60 * 60
CACHE_TIMEOUT_TEN_MINUTES = 10 * 60


def image_path(instance, filename):
    filename, file_extension = os.path.splitext(filename)
    clean_name = quote(quote(instance.name.encode('utf8')), '')
    clean_name = "%s_image_%s" % (clean_name.lower(), datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    name = "%s%s" % (str(clean_name), file_extension)
    return name


def nation_path(instance, filename):
    filename, file_extension = os.path.splitext(filename)
    clean_name = quote(quote(instance.name.encode('utf8')), '')
    clean_name = "%s_nation_%s" % (clean_name.lower(), datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    name = "%s%s" % (str(clean_name), file_extension)
    return name


def logo_path(instance, filename):
    filename, file_extension = os.path.splitext(filename)
    clean_name = quote(quote(instance.name.encode('utf8')), '')
    clean_name = "%s_logo_%s" % (clean_name.lower(), datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    name = "%s%s" % (str(clean_name), file_extension)
    return name


class Agency(models.Model):
    id = models.IntegerField(primary_key=True, editable=True)
    name = models.CharField(max_length=200)
    parent = models.ForeignKey('self', related_name='related_agencies', null=True, blank=True)
    featured = models.BooleanField(default=False)
    country_code = models.CharField(max_length=1048, blank=True, default="")
    abbrev = models.CharField(max_length=255, blank=True, default="")
    type = models.CharField(max_length=255, blank=True, null=True)
    agency_type = models.ForeignKey(AgencyType, related_name='agency', blank=True, null=True, on_delete=models.CASCADE)
    info_url = models.URLField(blank=True, null=True)
    wiki_url = models.URLField(blank=True, null=True)
    description = models.CharField(max_length=2048, blank=True, null=True, default=None)
    launchers = models.CharField(max_length=500, default='', blank=True)
    spacecraft = models.CharField(max_length=500, default='', blank=True)
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

        cache_key = "%s-%s" % (self.id, "agency-success")
        count = cache.get(cache_key)
        if count is not None:
            return count

        count = Launch.objects.filter(rocket__configuration__launch_agency__id=self.id).filter(status__id=3).count()
        related_agency = self.related_agencies.all()
        for related in related_agency:
            count += Launch.objects.filter(rocket__configuration__launch_agency__id=related.id).count()

        cache.set(cache_key, count, CACHE_TIMEOUT_ONE_DAY)

        return count

    @property
    def failed_launches(self):
        cache_key = "%s-%s" % (self.id, "agency-failed")
        count = cache.get(cache_key)
        if count is not None:
            return count

        count = Launch.objects.filter(rocket__configuration__launch_agency__id=self.id).filter(
            Q(status__id=4) | Q(status__id=7)).count()
        related_agency = self.related_agencies.all()
        for related in related_agency:
            count += Launch.objects.filter(rocket__configuration__launch_agency__id=related.id).filter(
                Q(status__id=4) | Q(status__id=7)).count()
        # set cal_date in cache for later use

        cache.set(cache_key, count, CACHE_TIMEOUT_ONE_DAY)

        return count

    @property
    def pending_launches(self):

        cache_key = "%s-%s" % (self.id, "agency-pending")
        count = cache.get(cache_key)
        if count is not None:
            return count

        count = Launch.objects.filter(rocket__configuration__launch_agency__id=self.id).filter(
            Q(status__id=1) | Q(status__id=2) | Q(status__id=5)).count()
        related_agency = self.related_agencies.all()
        for related in related_agency:
            count += Launch.objects.filter(rocket__configuration__launch_agency__id=related.id).filter(
                Q(status__id=1) | Q(status__id=2) | Q(status__id=5)).count()

        # set in cache for later use
        cache.set(cache_key, count, CACHE_TIMEOUT_ONE_DAY)

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


# The Spacecraft object is meant to define spacecraft (past and present) that are human-rated for spaceflight.
#
# Example: Dragon, Orion, etc.
class SpacecraftConfiguration(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    agency = models.CharField(max_length=200, default='Unknown')
    launch_agency = models.ForeignKey(Agency, related_name='spacecraft_list', blank=True, null=True)
    history = models.CharField(max_length=1000, default='')
    details = models.CharField(max_length=1000, default='')
    in_use = models.BooleanField(default=True)
    capability = models.CharField(max_length=2048, default='')
    maiden_flight = models.DateField(max_length=255, null=True)
    height = models.FloatField(verbose_name="Length (m)", blank=True, null=True)
    diameter = models.FloatField(verbose_name="Diameter (m)", blank=True, null=True)
    human_rated = models.BooleanField(default=False)
    crew_capacity = models.IntegerField(verbose_name="Crew Capacity", blank=True, null=True)
    payload_capacity = models.IntegerField(verbose_name="Payload Capacity (kg)", blank=True, null=True)
    flight_life = models.CharField(max_length=2048, blank=True, null=True)
    wiki_link = models.URLField(blank=True)
    info_link = models.URLField(blank=True)
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
        verbose_name = 'Spacecraft Configuration'
        verbose_name_plural = 'Spacecraft Configurations'


# The LauncherDetail object is meant to define orbital class launch vehicles (past and present).
#
# Example: Falcon 9, Saturn V, etc.
class LauncherConfig(models.Model):
    id = models.AutoField(primary_key=True)
    launch_library_id = models.IntegerField(null=True, blank=True)
    name = models.CharField(max_length=200)
    active = models.BooleanField(default=True)
    reusable = models.BooleanField(default=False)
    audited = models.BooleanField(default=False)
    librarian_notes = models.CharField(max_length=2048, default='', blank=True, null=True)
    description = models.CharField(max_length=2048, default='', blank=True)
    family = models.CharField(max_length=200, default='', blank=True)
    full_name = models.CharField(max_length=200, default='', blank=True)
    launch_agency = models.ForeignKey(Agency, related_name='launcher_list', blank=True, null=True)
    variant = models.CharField(max_length=200, default='', blank=True)
    alias = models.CharField(max_length=200, default='', blank=True)
    launch_cost = models.CharField(verbose_name="Launch Cost ($)", max_length=200, null=True, blank=True)
    maiden_flight = models.DateField(verbose_name="Maiden Flight Date", max_length=255, null=True, blank=True)
    min_stage = models.IntegerField(blank=True, null=True)
    max_stage = models.IntegerField(blank=True, null=True)
    length = models.FloatField(verbose_name="Length (m)", blank=True, null=True)
    diameter = models.FloatField(verbose_name="Max Diameter (m)", blank=True, null=True)
    fairing_diameter = models.FloatField(verbose_name="Max Fairing Diameter (m)", blank=True, null=True)
    launch_mass = models.IntegerField(verbose_name="Mass at Launch (T)", blank=True, null=True)
    leo_capacity = models.IntegerField(verbose_name="LEO Capacity (kg)", blank=True, null=True)
    gto_capacity = models.IntegerField(verbose_name="GTO Capacity (kg)", blank=True, null=True)
    geo_capacity = models.IntegerField(verbose_name="GEO Capacity (kg)", blank=True, null=True)
    sso_capacity = models.IntegerField(verbose_name="SSO Capacity (kg)", blank=True, null=True)
    to_thrust = models.IntegerField(verbose_name="Thrust at Liftoff (kN)", blank=True, null=True)
    apogee = models.IntegerField(verbose_name="Apogee - Sub-Orbital Only (km)", blank=True, null=True)
    vehicle_range = models.IntegerField(verbose_name="Vehicle Range - Legacy", blank=True, null=True)
    info_url = models.CharField(max_length=200, default='', blank=True, null=True)
    wiki_url = models.CharField(max_length=200, default='', blank=True, null=True)
    legacy_image_url = models.CharField(max_length=200, default='', blank=True)
    image_url = models.FileField(default=None, storage=LauncherImageStorage(), upload_to=image_path, null=True,
                                 blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name

    def __unicode__(self):
        return u'%s' % self.full_name

    class Meta:
        ordering = ['name']
        verbose_name = 'Launcher Configuration'
        verbose_name_plural = 'Launcher Configurations'


# The Events object is meant to define events (past and present).
# Example: Blue Origin Launches, ISS Crew returns, etc.
class Events(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=2048, default='', blank=True)
    location = models.CharField(max_length=100, default='', blank=True)
    feature_image = models.FileField(storage=EventImageStorage(), default=None, null=True, blank=True,
                                     upload_to=image_path)
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

    def __str__(self):
        return self.name

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

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = 'Pad'
        verbose_name_plural = 'Pads'


class Mission(models.Model):
    id = models.AutoField(primary_key=True)
    launch_library_id = models.IntegerField(editable=True, blank=True, null=True, unique=True)
    name = models.CharField(max_length=255, blank=True, default="")
    description = models.CharField(max_length=2048, blank=True, default="")
    type = models.IntegerField(blank=True, null=True)
    type_name = models.CharField(max_length=255, blank=True, default="")
    mission_type = models.ForeignKey(MissionType, related_name='mission', blank=True, null=True,
                                     on_delete=models.CASCADE)
    orbit = models.ForeignKey(Orbit, related_name='mission', null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        verbose_name = 'Mission'
        verbose_name_plural = 'Missions'


class Payload(models.Model):
    id = models.IntegerField(primary_key=True, editable=True)
    name = models.CharField(max_length=1048, blank=True, default="")
    description = models.CharField(max_length=2048, blank=True, default="")
    weight = models.CharField(max_length=255, blank=True, null=True)
    dimensions = models.CharField(max_length=255, blank=True, null=True)
    type = models.IntegerField(blank=True, null=True)
    total = models.IntegerField(blank=True, null=True)
    type_name = models.CharField(max_length=255, blank=True, default="")
    mission = models.ForeignKey(Mission, related_name='payloads', blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return u"%s" % self.name


class Launcher(models.Model):
    id = models.AutoField(primary_key=True)
    serial_number = models.CharField(max_length=10, blank=True, null=True)
    flight_proven = models.BooleanField(default=False)
    status = models.CharField(max_length=2048, blank=True, default="")
    details = models.CharField(max_length=2048, blank=True, default="")
    launcher_config = models.ForeignKey(LauncherConfig, related_name='launcher', null=True, on_delete=models.CASCADE)

    @property
    def previous_flights(self):

        cache_key = "%s-%s" % (self.id, "launcher")
        count = cache.get(cache_key)
        if count is not None:
            return count

        print("not in cache get from database")
        count = Launch.objects.values('id').filter(rocket__firststage__launcher__id=self.id).filter(
            Q(status__id=3) | Q(status__id=4) | Q(status__id=7)).count()

        # set cal_date in cache for later use
        cache.set(cache_key, count, CACHE_TIMEOUT_TEN_MINUTES)

        return count

    def __str__(self):
        if self.launcher_config is not None:
            return '%s (%s)' % (self.serial_number, self.launcher_config.full_name)
        else:
            return self.serial_number

    def __unicode__(self):
        if self.launcher_config is not None:
            return u'%s (%s)' % (self.serial_number, self.launcher_config.full_name)
        else:
            return u'%s' % self.serial_number

    class Meta:
        ordering = ['serial_number', ]
        verbose_name = 'Launch Vehicle'
        verbose_name_plural = 'Launch Vehicles'


class Landing(models.Model):
    attempt = models.NullBooleanField(blank=False, null=False, default=False)
    success = models.NullBooleanField(blank=True, null=True)
    description = models.CharField(max_length=2048, blank=True, default="")
    landing_type = models.ForeignKey(LandingType, related_name='landing', null=True, blank=True,
                                     on_delete=models.SET_NULL)
    landing_location = models.ForeignKey(LandingLocation, related_name='landing', null=True, blank=True,
                                         on_delete=models.SET_NULL)

    def __str__(self):
        try:
            if self.firststage is not None:
                return u"Landing: %s" % self.firststage
            elif self.secondstage is not None:
                return u"Landing: %s" % self.secondstage
            else:
                return u"(%d) Unassigned Landing" % self.id
        except (Launch.DoesNotExist, FirstStage.DoesNotExist) as e:
            return u"(%d) Unassigned Landing" % self.id

    def __unicode__(self):
        try:
            if self.firststage is not None:
                return u"Landing: %s" % self.firststage
            elif self.secondstage is not None:
                return u"Landing: %s" % self.secondstage
            else:
                return u"(%d) Unassigned Landing" % self.id
        except (Launch.DoesNotExist, FirstStage.DoesNotExist) as e:
            return u"(%d) Unassigned Landing" % self.id


class Rocket(models.Model):
    configuration = models.ForeignKey(LauncherConfig, related_name='rocket')

    def __str__(self):
        try:
            if self.launch is not None and self.launch.mission is not None:
                return u"%s: %s (Rocket)" % (self.id, self.launch.mission.name)
            elif self.launch is not None:
                return u"%s: %s (Rocket)" % (self.id, self.launch.name)
            else:
                return u"%s: Unsaved %s" % (self.id, self.configuration.name)
        except ObjectDoesNotExist:
            return u"%s: Unsaved %s" % (self.id, self.configuration.name)

    def __unicode__(self):
        try:
            if self.launch is not None and self.launch.mission is not None:
                return u"%s (Rocket)" % self.launch.mission.name
            elif self.launch is not None:
                return u"%s (Rocket)" % self.launch.name
            else:
                return u"Unsaved %s" % self.configuration.name
        except ObjectDoesNotExist:
            return u"Unsaved %s" % self.configuration.name


class SecondStage(models.Model):
    landing = models.OneToOneField(Landing, related_name='secondstage', null=True, blank=True,
                                   on_delete=models.SET_NULL)
    launcher = models.ForeignKey(Launcher, related_name='secondstage', on_delete=models.CASCADE)
    rocket = models.ForeignKey(Rocket, related_name='secondstage', on_delete=models.CASCADE)

    def __str__(self):
        try:
            if self.rocket is not None and self.rocket.launch is not None:
                return u"%s (%s)" % (self.rocket.launch.name, self.launcher.serial_number)
            else:
                return u"Unsaved %s" % self.launcher.serial_number
        except ObjectDoesNotExist:
            return u"Unsaved %s" % self.launcher.serial_number

    def __unicode__(self):
        try:
            if self.rocket is not None and self.rocket.launch is not None:
                return u"%s (%s)" % (self.rocket.launch.name, self.launcher.serial_number)
            else:
                return u"Unsaved %s" % self.launcher.serial_number
        except ObjectDoesNotExist:
            return u"Unsaved %s" % self.launcher.serial_number


class FirstStage(models.Model):
    type = models.ForeignKey(FirstStageType, related_name='firststage', on_delete=models.PROTECT)
    reused = models.NullBooleanField(null=True, blank=True)
    landing = models.OneToOneField(Landing, related_name='firststage', null=True, blank=True, on_delete=models.SET_NULL)
    launcher = models.ForeignKey(Launcher, related_name='firststage', on_delete=models.CASCADE)
    rocket = models.ForeignKey(Rocket, related_name='firststage', on_delete=models.CASCADE)

    @property
    def launcher_flight_number(self):
        count = Launch.objects.values('id').filter(rocket__firststage__launcher__id=self.launcher.id).filter(
            net__lte=F('net')).count()
        return count

    def __str__(self):
        try:
            if self.rocket is not None and self.rocket.launch is not None:
                return u"%s (%s)" % (self.rocket.launch.name, self.launcher.serial_number)
            else:
                return u"Unsaved %s" % self.launcher.serial_number
        except ObjectDoesNotExist:
            return u"Unsaved %s" % self.launcher.serial_number

    def __unicode__(self):
        try:
            if self.rocket is not None and self.rocket.launch is not None:
                return u"%s (%s)" % (self.rocket.launch.name, self.launcher.serial_number)
            else:
                return u"Unsaved %s" % self.launcher.serial_number
        except ObjectDoesNotExist:
            return u"Unsaved %s" % self.launcher.serial_number


class Astronauts(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False)
    date_of_birth = models.DateField(null=False, blank=False)
    date_of_death = models.DateField(null=True, blank=True)
    status = models.ForeignKey(AstronautStatus, on_delete=models.CASCADE,
                               null=False, blank=False)
    nationality = models.CharField(max_length=255, null=False,
                                   blank=False)
    agency = models.ForeignKey(Agency, on_delete=models.SET_NULL, null=True,
                               blank=True)
    twitter = models.CharField(max_length=255, null=True, blank=True)
    instagram = models.CharField(max_length=255, null=True, blank=True)
    bio = models.CharField(max_length=2048, null=False, blank=False)
    profile_image = models.FileField(default=None, storage=AstronautImageStorage(), upload_to=image_path, null=True,
                                     blank=True)
    wiki = models.CharField(max_length=255, null=True, blank=True)
    slug = models.SlugField(unique=True, max_length=100)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Astronauts, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return self.slug

    def get_full_absolute_url(self):
        return 'https://spacelaunchnow.me/astronaut/%s' % (self.get_absolute_url())

    @property
    def flights(self):
        listi = list((Launch.objects.filter(Q(rocket__spacecraftflight__launch_crew__id=self.pk) |
                                            Q(rocket__spacecraftflight__onboard_crew__id=self.pk) |
                                            Q(rocket__spacecraftflight__landing_crew__id=self.pk))
                      .values_list('pk', flat=True)
                      .distinct()))
        launches = Launch.objects.filter(pk__in=listi)
        return launches

    @property
    def age(self):
        import datetime
        return int((datetime.date.today() - self.date_of_birth).days / 365.25)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        verbose_name = 'Astronaut'
        verbose_name_plural = 'Astronauts'


class AstronautFlight(models.Model):
    role = models.ForeignKey(AstronautRole, null=True, blank=True, on_delete=models.CASCADE)
    astronaut = models.ForeignKey(Astronauts, on_delete=models.CASCADE)

    def __str__(self):
        return u'%s: %s' % (self.role, self.astronaut)

    def __unicode__(self):
        return u'%s: %s' % (self.role, self.astronaut)


class Spacecraft(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False)
    serial_number = models.CharField(max_length=255, null=True, blank=True)
    spacecraft_config = models.ForeignKey(SpacecraftConfiguration,
                                          null=False)
    description = models.CharField(max_length=2048, null=False, blank=False)
    status = models.ForeignKey(SpacecraftStatus, null=False, blank=False)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        verbose_name = 'Spacecraft'
        verbose_name_plural = 'Spacecrafts'


class SpaceStation(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False)
    founded = models.DateField(null=False, blank=False)
    owner = models.ForeignKey(Agency, blank=False, null=False)
    docked_vehicles = models.ManyToManyField(Spacecraft, blank=True, related_name='spacestation')
    description = models.CharField(max_length=2048, null=False, blank=False)
    orbit = models.CharField(max_length=255, null=False, blank=False)
    crew = models.ManyToManyField(Astronauts, blank=True)
    status = models.ForeignKey(SpaceStationStatus, null=False, blank=False)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        verbose_name = 'Space Station'
        verbose_name_plural = 'Space Stations'


class SpacecraftFlight(models.Model):
    splashdown = models.DateTimeField(null=True, blank=True)
    launch_crew = models.ManyToManyField(AstronautFlight,
                                         related_name='launch_crew',
                                         blank=True)
    onboard_crew = models.ManyToManyField(AstronautFlight,
                                          related_name='onboard_crew',
                                          blank=True)
    landing_crew = models.ManyToManyField(AstronautFlight,
                                          related_name='landing_crew',
                                          blank=True)
    spacecraft = models.ForeignKey(Spacecraft, on_delete=models.CASCADE)
    rocket = models.OneToOneField(Rocket, related_name='spacecraftflight', on_delete=models.CASCADE)
    destination = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.spacecraft.name

    def __unicode__(self):
        return u'%s' % self.spacecraft.name

    class Meta:
        verbose_name = 'Spacecraft Flight'
        verbose_name_plural = 'Spacecraft Flights'


class Launch(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    launch_library_id = models.IntegerField(editable=True, null=True, blank=True)
    launch_library = models.NullBooleanField(default=False)
    name = models.CharField(max_length=2048, blank=True)
    img_url = models.CharField(max_length=1048, blank=True, null=True)
    status = models.ForeignKey(LaunchStatus, related_name='launch', blank=True, null=True, on_delete=models.SET_NULL)
    net = models.DateTimeField(max_length=255, null=True)
    window_end = models.DateTimeField(max_length=255, null=True)
    window_start = models.DateTimeField(max_length=255, null=True)
    inhold = models.NullBooleanField(default=False)
    tbdtime = models.NullBooleanField(default=False)
    tbddate = models.NullBooleanField(default=False)
    probability = models.IntegerField(blank=True, null=True)
    holdreason = models.CharField(max_length=2048, blank=True, null=True)
    failreason = models.CharField(max_length=2048, blank=True, null=True)
    hashtag = models.CharField(max_length=2048, blank=True, null=True)
    slug = models.SlugField(unique=True, max_length=1048)
    rocket = models.OneToOneField(Rocket, blank=True, null=True, related_name='launch', unique=True)
    pad = models.ForeignKey(Pad, related_name='launch', null=True, on_delete=models.SET_NULL)
    mission = models.ForeignKey(Mission, related_name='launch', null=True, on_delete=models.SET_NULL)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return u'%s' % self.name

    def save(self, *args, **kwargs):
        if self.launch_library and self.launch_library_id is not None:
            self.slug = slugify(self.name + "-" + str(self.launch_library_id))
        else:
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

    def __str__(self):
        return self.vid_url

    def __unicode__(self):
        return u'%s' % self.vid_url

    class Meta:
        verbose_name = 'Video URL'
        verbose_name_plural = 'Video URLs'


class InfoURLs(models.Model):
    info_url = models.URLField(max_length=200)
    launch = models.ForeignKey(Launch, related_name='info_urls', on_delete=models.CASCADE)

    def __str__(self):
        return self.info_url

    def __unicode__(self):
        return u'%s' % self.info_url

    class Meta:
        verbose_name = 'Info URL'
        verbose_name_plural = 'Info URLs'
