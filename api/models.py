# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import uuid

from django_extensions.db.fields import AutoSlugField

from api.utils.utilities import resize_for_upload, resize_needed, get_map_url, get_pad_url

try:
    from urllib import quote  # Python 2.X
except ImportError:
    from urllib.parse import quote  # Python 3+

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q, F
from django.db.models.functions import datetime

from configurations.models import *
from custom_storages import LogoStorage, AgencyImageStorage, OrbiterImageStorage, LauncherImageStorage, \
    AgencyNationStorage, EventImageStorage, AstronautImageStorage, SpaceStationImageStorage, LauncherCoreImageStorage, \
    LaunchImageStorage

# The Agency object is meant to define a agency that operates launchers and spacecrafts.
#
# Example: SpaceX has Falcon 9 Launchers and Dragon spacecrafts
#
from django.template.defaultfilters import truncatechars, slugify

CACHE_TIMEOUT_ONE_DAY = 24 * 60 * 60
CACHE_TIMEOUT_TEN_MINUTES = 10 * 60
CACHE_TIMEOUT_ONE_HOUR = 60 * 60


def image_path(instance, filename):
    filename, file_extension = os.path.splitext(filename)
    clean_name = quote(quote(instance.name.encode('utf8')), '')
    clean_name = "%s_image_%s" % (clean_name.lower(), datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    name = "%s%s" % (str(clean_name), file_extension)
    return name


def location_path(instance, filename):
    filename, file_extension = os.path.splitext(filename)
    clean_name = quote(quote(instance.name.encode('utf8')), '')
    clean_name = "location_%s" % (clean_name.lower())
    name = "%s%s" % (str(clean_name[:15]), file_extension)
    return name


def pad_path(instance, filename):
    filename, file_extension = os.path.splitext(filename)
    clean_name = quote(quote(instance.name.encode('utf8')), '')
    clean_name = "pad_%s" % (clean_name.lower())
    name = "%s%s" % (str(clean_name[:15]), file_extension)
    return name


def launch_image_path(instance, filename):
    filename, file_extension = os.path.splitext(filename)
    clean_name = quote(quote(instance.name.encode('utf8')), '')
    clean_name = "%s_image_%s" % (clean_name.lower(), datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    name = "%s%s" % (str(clean_name), file_extension)
    return name


def infographic_image_path(instance, filename):
    filename, file_extension = os.path.splitext(filename)
    clean_name = quote(quote(instance.name.encode('utf8')), '')
    clean_name = "%s_infographic_%s" % (clean_name.lower()[:15], datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    name = "%s%s" % (str(clean_name), file_extension)
    return name


def launcher_path(instance, filename):
    filename, file_extension = os.path.splitext(filename)
    clean_name = str(instance.id)
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

    def save(self, **kwargs):
        if resize_needed(self.image_url):
            self.image_url = resize_for_upload(self.image_url)
        if resize_needed(self.logo_url):
            self.logo_url = resize_for_upload(self.logo_url)
        if resize_needed(self.nation_url):
            self.nation_url = resize_for_upload(self.nation_url)
        super(Agency, self).save()

    @property
    def total_launch_count(self):
        cache_key = "%s-%s" % (self.id, "agency-total_launch_count")
        count = cache.get(cache_key)
        if count is not None:
            return count

        now = datetime.datetime.now(tz=utc)
        count = Launch.objects.filter(rocket__configuration__manufacturer__id=self.id).filter(net__lte=now).order_by('-net').count()
        related_agency = self.related_agencies.all()
        for related in related_agency:
            count += Launch.objects.filter(rocket__configuration__manufacturer__id=related.id).count()
        cache.set(cache_key, count, CACHE_TIMEOUT_ONE_DAY)
        return count

    @property
    def consecutive_successful_launches(self):
        cache_key = "%s-%s" % (self.id, "agency-consecutive-success")
        count = cache.get(cache_key)
        if count is not None:
            return count

        count = 0
        now = datetime.datetime.now(tz=utc)
        launches = Launch.objects.filter(rocket__configuration__manufacturer__id=self.id).filter(Q(status__id=3)|Q(status__id=4)|Q(status__id=7)).filter(net__lte=now).order_by('-net')
        for launch in launches:
            if launch.status.id == 3:
                count += 1
            else:
                break

        related_agency = self.related_agencies.all()
        for related in related_agency:
            launches = Launch.objects.filter(rocket__configuration__manufacturer__id=related.id).filter(Q(status__id=3)|Q(status__id=4)|Q(status__id=7)).filter(net__lte=now).order_by('-net')
            for launch in launches:
                if launch.status.id == 3:
                    count += 1
                else:
                    break

        cache.set(cache_key, count, CACHE_TIMEOUT_ONE_DAY)
        return count

    @property
    def successful_landings(self):
        cache_key = "%s-%s" % (self.id, "agency-successful-landings")
        count = cache.get(cache_key)
        if count is not None:
            return count

        now = datetime.datetime.now(tz=utc)
        count = Launch.objects.filter(launch_service_provider__id=self.id).filter(net__lte=now).filter(
            rocket__firststage__landing__success=True).order_by('-net').count()
        cache.set(cache_key, count, CACHE_TIMEOUT_ONE_HOUR)
        return count

    @property
    def failed_landings(self):
        cache_key = "%s-%s" % (self.id, "agency-failed-landings")
        count = cache.get(cache_key)
        if count is not None:
            return count

        now = datetime.datetime.now(tz=utc)
        count = Launch.objects.filter(launch_service_provider__id=self.id).filter(net__lte=now).filter(
            rocket__firststage__landing__success=False).order_by('-net').count()
        cache.set(cache_key, count, CACHE_TIMEOUT_ONE_HOUR)
        return count

    @property
    def attempted_landings(self):
        cache_key = "%s-%s" % (self.id, "agency-attempted-landings")
        count = cache.get(cache_key)
        if count is not None:
            return count

        now = datetime.datetime.now(tz=utc)
        count = Launch.objects.filter(launch_service_provider__id=self.id).filter(net__lte=now).filter(
            rocket__firststage__landing__attempt=True).order_by('-net').count()
        cache.set(cache_key, count, CACHE_TIMEOUT_ONE_HOUR)
        return count

    @property
    def consecutive_successful_landings(self):
        cache_key = "%s-%s" % (self.id, "agency-consecutive-landings")
        count = cache.get(cache_key)
        if count is not None:
            return count

        now = datetime.datetime.now(tz=utc)
        launches = Launch.objects.filter(launch_service_provider__id=self.id).filter(net__lte=now).order_by('-net')
        count = 0
        for launch in launches:
            for stage in launch.rocket.firststage.all():
                if stage.landing.attempt and stage.landing.success:
                    count += 1
                elif stage.landing.attempt and not stage.landing.success:
                    break
            else:
                continue
            break
        cache.set(cache_key, count, CACHE_TIMEOUT_ONE_HOUR)
        return count

    @property
    def successful_launches(self):
        cache_key = "%s-%s" % (self.id, "agency-success")
        count = cache.get(cache_key)
        if count is not None:
            return count

        count = Launch.objects.filter(rocket__configuration__manufacturer__id=self.id).filter(status__id=3).count()
        related_agency = self.related_agencies.all()
        for related in related_agency:
            count += Launch.objects.filter(rocket__configuration__manufacturer__id=related.id).filter(status__id=3).count()

        cache.set(cache_key, count, CACHE_TIMEOUT_ONE_DAY)

        return count

    @property
    def failed_launches(self):
        cache_key = "%s-%s" % (self.id, "agency-failed")
        count = cache.get(cache_key)
        if count is not None:
            return count

        count = Launch.objects.filter(rocket__configuration__manufacturer__id=self.id).filter(
            Q(status__id=4) | Q(status__id=7)).count()
        related_agency = self.related_agencies.all()
        for related in related_agency:
            count += Launch.objects.filter(rocket__configuration__manufacturer__id=related.id).filter(
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

        count = Launch.objects.filter(rocket__configuration__manufacturer__id=self.id).filter(
            Q(status__id=1) | Q(status__id=2) | Q(status__id=5)).count()
        related_agency = self.related_agencies.all()
        for related in related_agency:
            count += Launch.objects.filter(rocket__configuration__manufacturer__id=related.id).filter(
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


def get_default_config_type():
    obj, created = SpacecraftConfigurationType.objects.get_or_create(id=1, name="Unknown")
    return obj.id


# The Spacecraft object is meant to define spacecraft (past and present) that are human-rated for spaceflight.
# Example: Dragon, Orion, etc.
class SpacecraftConfiguration(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    type = models.ForeignKey(SpacecraftConfigurationType, default=get_default_config_type)
    agency = models.CharField(max_length=200, default='Unknown')
    manufacturer = models.ForeignKey(Agency, related_name='spacecraft_list', blank=True, null=True)
    history = models.CharField(max_length=1000, default='')
    details = models.CharField(max_length=1000, default='')
    in_use = models.BooleanField(default=True)
    capability = models.CharField(max_length=2048, default='')
    maiden_flight = models.DateField(max_length=255, null=True, blank=True)
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

    def save(self, **kwargs):
        if resize_needed(self.image_url):
            self.image_url = resize_for_upload(self.image_url)
        if resize_needed(self.nation_url):
            self.nation_url = resize_for_upload( self.nation_url)
        super(SpacecraftConfiguration, self).save()

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
    manufacturer = models.ForeignKey(Agency, related_name='launcher_list', blank=True, null=True)
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

    @property
    def total_launch_count(self):
        cache_key = "%s-%s" % (self.id, "launcherconfig-total")
        count = cache.get(cache_key)
        if count is not None:
            return count

        now = datetime.datetime.now(tz=utc)
        count = Launch.objects.filter(rocket__configuration__id=self.id).filter(net__lte=now).count()
        cache.set(cache_key, count, CACHE_TIMEOUT_ONE_DAY)
        return count

    @property
    def consecutive_successful_launches(self):
        cache_key = "%s-%s" % (self.id, "launcherconfig-consecutive-success")
        count = cache.get(cache_key)
        if count is not None:
            return count

        count = 0
        now = datetime.datetime.now(tz=utc)
        launches = Launch.objects.filter(rocket__configuration__id=self.id).filter(Q(status__id=3)|Q(status__id=4)|Q(status__id=7)).filter(net__lte=now).order_by('-net')
        for launch in launches:
            if launch.status.id == 3:
                count += 1
            else:
                break
        cache.set(cache_key, count, CACHE_TIMEOUT_ONE_DAY)
        return count

    @property
    def successful_launches(self):
        cache_key = "%s-%s" % (self.id, "launcherconfig-success")
        count = cache.get(cache_key)
        if count is not None:
            return count

        count = Launch.objects.filter(rocket__configuration__id=self.id).filter(status__id=3).count()
        cache.set(cache_key, count, CACHE_TIMEOUT_ONE_DAY)
        return count

    @property
    def failed_launches(self):
        cache_key = "%s-%s" % (self.id, "launcherconfig-failed")
        count = cache.get(cache_key)
        if count is not None:
            return count

        count = Launch.objects.filter(rocket__configuration__id=self.id).filter(
            Q(status__id=4) | Q(status__id=7)).count()
        cache.set(cache_key, count, CACHE_TIMEOUT_ONE_DAY)
        return count

    @property
    def pending_launches(self):
        cache_key = "%s-%s" % (self.id, "launcherconfig-pending")
        count = cache.get(cache_key)
        if count is not None:
            return count

        count = Launch.objects.filter(rocket__configuration__id=self.id).filter(
            Q(status__id=1) | Q(status__id=2) | Q(status__id=5)).count()
        cache.set(cache_key, count, CACHE_TIMEOUT_ONE_DAY)
        return count

    def save(self, **kwargs):
        if resize_needed(self.image_url):
            self.image_url = resize_for_upload(self.image_url)
        super(LauncherConfig, self).save()


def get_default_event_config_type():
    obj, created = EventType.objects.get_or_create(id=1, name="Unknown")
    return obj.id


# The Events object is meant to define events (past and present).
# Example: ISS Crew returns, etc.
class Events(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=2048, default='', blank=True)
    type = models.ForeignKey(EventType, default=get_default_event_config_type)
    location = models.CharField(max_length=100, default='', blank=True, null=True)
    news_url = models.URLField(max_length=250, blank=True, null=True)
    video_url = models.URLField(max_length=250, blank=True, null=True)
    webcast_live = models.BooleanField(default=False)
    feature_image = models.FileField(storage=EventImageStorage(), default=None, null=True, blank=True,
                                     upload_to=image_path)
    slug = AutoSlugField(populate_from=['name'], overwrite=True)
    expedition = models.ManyToManyField('Expedition', blank=True)
    spacestation = models.ManyToManyField('Spacestation', blank=True)
    launch = models.ManyToManyField('Launch', blank=True)
    date = models.DateTimeField(blank=True, null=True)

    notifications_enabled = models.BooleanField(blank=True, default=False)

    was_notified_ten_minutes = models.BooleanField(blank=True, default=False)
    was_notified_webcast_live = models.BooleanField(blank=True, default=False)

    was_tweeted_ten_minutes = models.BooleanField(blank=True, default=False)
    was_tweeted_webcast_live = models.BooleanField(blank=True, default=False)

    was_discorded_ten_minutes = models.BooleanField(blank=True, default=False)
    was_discorded_webcast_live = models.BooleanField(blank=True, default=False)

    last_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        ordering = ['name']
        verbose_name = 'Event'
        verbose_name_plural = 'Events'

    def save(self, **kwargs):
        if resize_needed(self.feature_image):
            self.feature_image = resize_for_upload(self.feature_image)
        super(Events, self).save()

    def get_absolute_url(self):
        return self.slug

    def get_full_absolute_url(self):
        return 'https://spacelaunchnow.me/event/%s' % (self.get_absolute_url())


class Location(models.Model):
    id = models.AutoField(primary_key=True)
    launch_library_id = models.IntegerField(blank=True, null=True, unique=True)
    name = models.CharField(max_length=255, blank=True, default="")
    country_code = models.CharField(max_length=255, blank=True, default="")
    map_image = models.FileField(default=None, storage=LaunchImageStorage(), upload_to=location_path,
                                 null=True, blank=True)

    @property
    def total_launch_count(self):
        cache_key = "%s-%s" % (self.id, "location-total")
        count = cache.get(cache_key)
        if count is not None:
            return count

        now = datetime.datetime.now(tz=utc)
        count = Launch.objects.filter(pad__location__id=self.id).filter(net__lte=now).count()
        cache.set(cache_key, count, CACHE_TIMEOUT_ONE_DAY)
        return count

    @property
    def total_landing_count(self):
        cache_key = "%s-%s" % (self.id, "location-total")
        count = cache.get(cache_key)
        if count is not None:
            return count

        now = datetime.datetime.now(tz=utc)
        count = Launch.objects.filter(rocket__firststage__landing__landing_location__location__id=self.id).filter(net__lte=now).count()
        cache.set(cache_key, count, CACHE_TIMEOUT_ONE_DAY)
        return count

    def save(self, *args, **kwargs):
        if not self.map_image:
            get_map_url(self)
        super(Location, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = 'Location'
        verbose_name_plural = 'Locations'


class Pad(models.Model):
    id = models.AutoField(primary_key=True)
    launch_library_id = models.IntegerField(blank=True, null=True)
    agency_id = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, default="")
    info_url = models.URLField(blank=True, null=True)
    wiki_url = models.URLField(blank=True, null=True)
    map_url = models.URLField(blank=True, null=True)
    latitude = models.CharField(blank=True, null=True, max_length=30)
    longitude = models.CharField(blank=True, null=True, max_length=30)
    location = models.ForeignKey(Location, related_name='pad', blank=True, null=True, on_delete=models.CASCADE)
    map_image = models.FileField(default=None, storage=LaunchImageStorage(), upload_to=pad_path,
                                 null=True, blank=True)

    @property
    def orbital_launch_attempt_count(self):
        cache_key = "%s-%s" % (self.id, "pad-launch-attempt-count")
        count = cache.get(cache_key)
        if count is not None:
            return count

        now = datetime.datetime.now(tz=utc)
        start_of_year = datetime.datetime(year=now.year, month=1, day=1)
        count = Launch.objects.filter(net__gte=start_of_year, net__lte=now, pad__id=self.id).filter(~Q(mission__orbit__name="Sub-Orbital")).count()
        cache.set(cache_key, count, CACHE_TIMEOUT_ONE_DAY)
        return count

    @property
    def total_launch_count(self):
        cache_key = "%s-%s" % (self.id, "pad-total")
        count = cache.get(cache_key)
        if count is not None:
            return count

        now = datetime.datetime.now(tz=utc)
        count = Launch.objects.filter(pad__id=self.id).filter(net__lte=now).count()
        cache.set(cache_key, count, CACHE_TIMEOUT_ONE_DAY)
        return count

    def save(self, *args, **kwargs):
        if not self.map_image:
            get_pad_url(self)
        super(Pad, self).save(*args, **kwargs)

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
    image_url = models.FileField(default=None, storage=LauncherCoreImageStorage(), upload_to=launcher_path, null=True,
                                 blank=True)
    launcher_config = models.ForeignKey(LauncherConfig, related_name='launcher', null=True, on_delete=models.CASCADE)

    @property
    def successful_landings(self):
        cache_key = "%s-%s" % (self.id, "stage_successful_landings")
        res = cache.get(cache_key)
        if res:
            return res

        now = datetime.datetime.now(tz=utc)
        landings = Landing.objects.values('id').filter(firststage__launcher__id=self.id,
                                                       success=True, firststage__rocket__launch__net__lte=now).count()
        cache.set(cache_key, landings, CACHE_TIMEOUT_ONE_HOUR)
        return landings

    @property
    def attempted_landings(self):
        cache_key = "%s-%s" % (self.id, "stage_attempted_landings")
        res = cache.get(cache_key)
        if res:
            return res

        now = datetime.datetime.now(tz=utc)
        landings = Landing.objects.values('id').filter(firststage__launcher__id=self.id,
                                                       attempt=True, firststage__rocket__launch__net__lte=now).count()
        cache.set(cache_key, landings, CACHE_TIMEOUT_ONE_HOUR)
        return landings

    @property
    def flights(self):

        cache_key = "%s-%s" % (self.id, "launcher_flights")
        count = cache.get(cache_key)
        if count is not None:
            return count
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

    def save(self, *args, **kwargs):
        if resize_needed(self.image_url):
            self.image_url = resize_for_upload(self.image_url)
        super(Launcher, self).save(*args, **kwargs)


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


def previous_flight_id(self_ref):
    cache_key = "%s-%s" % (self_ref.id, "previous_flight_id")
    res = cache.get(cache_key)
    if res:
        return res

    launch_net = Launch.objects.get(id=self_ref.rocket.launch.id).net
    last_launch = Launch.objects.filter(rocket__firststage__launcher__id=self_ref.launcher.id).filter(net__lt=launch_net).order_by('-net').first()

    if last_launch:
        res = last_launch.id

    cache.set(cache_key, res, CACHE_TIMEOUT_ONE_DAY)
    return res


class FirstStage(models.Model):
    type = models.ForeignKey(FirstStageType, related_name='firststage', on_delete=models.PROTECT)
    reused = models.NullBooleanField(null=True, blank=True)
    landing = models.OneToOneField(Landing, related_name='firststage', null=True, blank=True, on_delete=models.SET_NULL)
    launcher = models.ForeignKey(Launcher, related_name='firststage', on_delete=models.CASCADE)
    rocket = models.ForeignKey(Rocket, related_name='firststage', on_delete=models.CASCADE)

    @property
    def previous_flight(self):
        flight_id = previous_flight_id(self)
        if previous_flight_id:
            return Launch.objects.get(id=flight_id)

        return None

    @property
    def previous_flight_date(self):
        cache_key = "%s-%s" % (self.id, "previous_flight_date")
        res = cache.get(cache_key)
        if res:
            return res

        last_launch_id = previous_flight_id(self)
        if last_launch_id:
            res = Launch.objects.get(id=last_launch_id).net

        cache.set(cache_key, res, CACHE_TIMEOUT_ONE_DAY)
        return res

    @property
    def turn_around_time_days(self):
        cache_key = "%s-%s" % (self.id, "turn_around_time_days")
        res = cache.get(cache_key)
        if res:
            return res

        launch_net = Launch.objects.get(id=self.rocket.launch.id).net
        if launch_net and self.previous_flight_date:
            turn_around = launch_net - self.previous_flight_date
            res = turn_around.days

        cache.set(cache_key, res, CACHE_TIMEOUT_ONE_DAY)
        return res

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


def get_default_astronaut_config_type():
    obj, created = AstronautType.objects.get_or_create(id=1, name="Unknown")
    return obj.id


class Astronaut(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False)
    date_of_birth = models.DateField(null=False, blank=False)
    date_of_death = models.DateField(null=True, blank=True)
    status = models.ForeignKey(AstronautStatus, on_delete=models.CASCADE,
                               null=False, blank=False)
    type = models.ForeignKey(AstronautType, on_delete=models.CASCADE, default=get_default_astronaut_config_type)
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
        if resize_needed(self.profile_image):
            self.profile_image = resize_for_upload(self.profile_image)
        super(Astronaut, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return self.slug

    def get_full_absolute_url(self):
        return 'https://spacelaunchnow.me/astronaut/%s' % (self.get_absolute_url())

    @property
    def flights(self):
        listi = list((Launch.objects.filter(rocket__spacecraftflight__launch_crew__astronaut__id=self.id)
                      .values_list('id', flat=True)
                      .distinct()))
        launches = Launch.objects.filter(id__in=listi).order_by('net')
        return launches

    @property
    def landings(self):
        listi = list((SpacecraftFlight.objects.filter(landing_crew__astronaut__id=self.id)
                      .values_list('id', flat=True)
                      .distinct()))
        landings = SpacecraftFlight.objects.filter(id__in=listi).order_by(
            'mission_end')
        return landings

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
        verbose_name_plural = 'Astronaut'


class AstronautFlight(models.Model):
    role = models.ForeignKey(AstronautRole, null=True, blank=True, on_delete=models.CASCADE)
    astronaut = models.ForeignKey(Astronaut, on_delete=models.CASCADE)

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


class SpacecraftFlight(models.Model):
    mission_end = models.DateTimeField(null=True, blank=True)
    launch_crew = models.ManyToManyField(AstronautFlight,
                                         related_name='launch_crew',
                                         blank=True)
    onboard_crew = models.ManyToManyField(AstronautFlight,
                                          related_name='onboard_crew',
                                          blank=True)
    landing_crew = models.ManyToManyField(AstronautFlight,
                                          related_name='landing_crew',
                                          blank=True)
    spacecraft = models.ForeignKey(Spacecraft, related_name='spacecraftflight', on_delete=models.CASCADE)
    rocket = models.OneToOneField(Rocket, related_name='spacecraftflight', on_delete=models.CASCADE)
    destination = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.spacecraft.name + self.rocket.__str__()

    def __unicode__(self):
        return u'%s' % self.spacecraft.name + self.rocket.__str__()

    class Meta:
        verbose_name = 'Spacecraft Flight'
        verbose_name_plural = 'Spacecraft Flights'


class SpaceStation(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False)
    founded = models.DateField(null=False, blank=False)
    deorbited = models.DateField(null=True, blank=True)
    owners = models.ManyToManyField(Agency, blank=False)
    description = models.CharField(max_length=2048, null=False, blank=False)
    orbit = models.ForeignKey(Orbit, null=False, blank=False)
    status = models.ForeignKey(SpaceStationStatus, null=False, blank=False)
    type = models.ForeignKey(SpaceStationType, null=False, blank=False, default=1)
    height = models.FloatField(verbose_name="Height (m)", blank=True, null=True)
    width = models.FloatField(verbose_name="Width (m)", blank=True, null=True)
    mass = models.FloatField(verbose_name="Mass (T)", blank=True, null=True)
    volume = models.IntegerField(verbose_name="Volume (m^3)", blank=True, null=True)
    image_url = models.FileField(default=None, storage=SpaceStationImageStorage(), upload_to=image_path, null=True,
                                 blank=True)
    active_expeditions = models.ManyToManyField('Expedition', blank=True)

    def save(self, *args, **kwargs):
        if resize_needed(self.image_url):
            self.image_url = resize_for_upload(self.image_url)
        super(SpaceStation, self).save(*args, **kwargs)

    @property
    def onboard_crew(self):
        count = 0
        onboard = Astronaut.objects.values('id').filter(astronautflight__expeditions__in=self.active_expeditions.all()).count()
        count += onboard
        return count

    @property
    def docked_vehicles(self):
        spacecraft = SpacecraftFlight.objects.filter(docking_events__space_station=self.id, docking_events__docked=True).distinct()
        return spacecraft

    def __str__(self):
        return self.name

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        verbose_name = 'Space Station'
        verbose_name_plural = 'Space Stations'


class Expedition(models.Model):
    space_station = models.ForeignKey(SpaceStation, on_delete=models.CASCADE,
                                      related_name='expeditions')
    name = models.CharField(max_length=255, null=False, blank=False)
    start = models.DateTimeField(null=False, blank=False)
    end = models.DateTimeField(null=True, blank=True)
    crew = models.ManyToManyField(AstronautFlight, related_name='expeditions')

    def __str__(self):
        return self.name

    def __unicode__(self):
        return u'%s' % self.name


class DockingEvent(models.Model):
    space_station = models.ForeignKey(SpaceStation, on_delete=models.CASCADE,
                                     related_name='docking_events')
    flight_vehicle = models.ForeignKey(SpacecraftFlight, on_delete=models.CASCADE,
                                       related_name='docking_events')
    docked = models.BooleanField(default=False)
    docking = models.DateTimeField(null=False, blank=False)
    departure = models.DateTimeField(null=True, blank=True)
    docking_location = models.ForeignKey(DockingLocation, null=False, blank=False)

    def __str__(self):
        return '{}-{}'.format(self.flight_vehicle.__str__(), self.docking)

    def __unicode__(self):
        return '{}-{}'.format(self.flight_vehicle.__str__(), self.docking)


class Launch(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    launch_library_id = models.IntegerField(editable=True, null=True, blank=True, unique=True)
    launch_library = models.NullBooleanField(default=False)
    webcast_live = models.BooleanField(default=False)
    name = models.CharField(max_length=2048, blank=True)
    status = models.ForeignKey(LaunchStatus, related_name='launch', blank=True, null=True, on_delete=models.SET_NULL)
    net = models.DateTimeField(max_length=255, null=True)
    window_end = models.DateTimeField(max_length=255, null=True)
    window_start = models.DateTimeField(max_length=255, null=True)
    inhold = models.NullBooleanField(default=False)
    tbdtime = models.NullBooleanField(default=False)
    tbddate = models.NullBooleanField(default=False)
    image_url = models.ImageField(default=None, storage=LaunchImageStorage(), upload_to=launch_image_path, null=True, blank=True)
    infographic_url = models.ImageField(default=None, storage=LaunchImageStorage(), upload_to=infographic_image_path, null=True, blank=True)
    probability = models.IntegerField(blank=True, null=True)
    holdreason = models.CharField(max_length=2048, blank=True, null=True)
    failreason = models.CharField(max_length=2048, blank=True, null=True)
    hashtag = models.CharField(max_length=2048, blank=True, null=True)
    slug = AutoSlugField(populate_from=['name'], overwrite=True, allow_duplicates=False, allow_unicode=False)
    rocket = models.OneToOneField(Rocket, blank=True, null=True, related_name='launch', unique=True)
    pad = models.ForeignKey(Pad, related_name='launch', null=True, on_delete=models.SET_NULL)
    mission = models.ForeignKey(Mission, related_name='launch', null=True, blank=True, on_delete=models.SET_NULL)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    launch_service_provider = models.ForeignKey(Agency, on_delete=models.SET_NULL, null=True, blank=True,
                                                verbose_name="Launch Service Provider")

    def __str__(self):
        return self.name

    def __unicode__(self):
        return u'%s' % self.name

    def save(self, *args, **kwargs):
        if self.launch_library_id is not None:
            self.launch_library = True
        super(Launch, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return self.slug

    def get_full_absolute_url(self):
        return 'https://spacelaunchnow.me/launch/%s' % (self.get_absolute_url())

    def get_admin_url(self):
        return "https://spacelaunchnow.me/admin/api/launch/%s/change" % self.id

    @property
    def img_url(self):
        return None

    @property
    def orbital_launch_attempt_count(self):
        cache_key = "%s-%s" % (self.id, "launches-orbital-launch-attempt-count")
        count = cache.get(cache_key)
        if count is not None:
            return count

        if not self.mission.orbit or self.mission.orbit.name != "Sub-Orbital":
            count = Launch.objects.filter(net__lte=self.net).filter(~Q(mission__orbit__name="Sub-Orbital")).count()
        else:
            count = None
        cache.set(cache_key, count, CACHE_TIMEOUT_ONE_DAY)
        return count

    @property
    def location_launch_attempt_count(self):
        cache_key = "%s-%s" % (self.id, "location-launch-attempt-count")
        count = cache.get(cache_key)
        if count is not None:
            return count

        count = Launch.objects.filter(net__lte=self.net, pad__location__id=self.pad.location.id).count()
        cache.set(cache_key, count, CACHE_TIMEOUT_ONE_DAY)
        return count

    @property
    def pad_launch_attempt_count(self):
        cache_key = "%s-%s" % (self.id, "pad-launch-attempt-count")
        count = cache.get(cache_key)
        if count is not None:
            return count

        count = Launch.objects.filter(net__lte=self.net, pad__id=self.pad.id).count()
        cache.set(cache_key, count, CACHE_TIMEOUT_ONE_DAY)
        return count

    @property
    def agency_launch_attempt_count(self):
        cache_key = "%s-%s" % (self.id, "agency-launch-attempt-count")
        count = cache.get(cache_key)
        if count is not None:
            return count

        count = Launch.objects.filter(net__lte=self.net,
                                      launch_service_provider__id=self.launch_service_provider.id).count()
        cache.set(cache_key, count, CACHE_TIMEOUT_ONE_DAY)
        return count

    @property
    def orbital_launch_attempt_count_year(self):
        cache_key = "%s-%s" % (self.id, "launches-orbital-launch-attempt-count-year")
        count = cache.get(cache_key)
        if count is not None:
            return count

        if not self.mission.orbit or self.mission.orbit.name != "Sub-Orbital":
            start_of_year = datetime.datetime(year=self.net.year, month=1, day=1)
            count = Launch.objects.filter(net__gte=start_of_year, net__lte=self.net).filter(~Q(mission__orbit__name="Sub-Orbital")).count()
        else:
            count = None
        cache.set(cache_key, count, CACHE_TIMEOUT_ONE_DAY)
        return count

    @property
    def location_launch_attempt_count_year(self):
        cache_key = "%s-%s" % (self.id, "location-launch-attempt-count-year")
        count = cache.get(cache_key)
        if count is not None:
            return count

        start_of_year = datetime.datetime(year=self.net.year, month=1, day=1)
        count = Launch.objects.filter(net__gte=start_of_year, net__lte=self.net, pad__location__id=self.pad.location.id).count()
        cache.set(cache_key, count, CACHE_TIMEOUT_ONE_DAY)
        return count

    @property
    def pad_launch_attempt_count_year(self):
        cache_key = "%s-%s" % (self.id, "pad-launch-attempt-count-year")
        count = cache.get(cache_key)
        if count is not None:
            return count

        start_of_year = datetime.datetime(year=self.net.year, month=1, day=1)
        count = Launch.objects.filter(net__gte=start_of_year, net__lte=self.net, pad__id=self.pad.id).count()
        cache.set(cache_key, count, CACHE_TIMEOUT_ONE_DAY)
        return count

    @property
    def agency_launch_attempt_count_year(self):
        cache_key = "%s-%s" % (self.id, "agency-launch-attempt-count-year")
        count = cache.get(cache_key)
        if count is not None:
            return count

        start_of_year = datetime.datetime(year=self.net.year, month=1, day=1)
        count = Launch.objects.filter(net__gte=start_of_year, net__lte=self.net,
                                      launch_service_provider__id=self.launch_service_provider.id).count()
        cache.set(cache_key, count, CACHE_TIMEOUT_ONE_DAY)
        return count

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
