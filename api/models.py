# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


# The Agency object is meant to define a agency that operates launchers and orbiters.
#
# Example: SpaceX has Falcon 9 Launchers and Dragon orbiters
#
from django.template.defaultfilters import truncatechars


class Agency(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=2048, blank=True, null=True, default=None)
    launchers = models.CharField(max_length=500, default='', blank=True)
    orbiters = models.CharField(max_length=500, default='', blank=True)
    image_url = models.URLField(blank=True, null=True, default=None)
    nation_url = models.URLField(blank=True, null=True, default=None)
    ceo = models.CharField(max_length=200, blank=True, null=True, default=None)
    founding_year = models.CharField(blank=True, null=True, default=None, max_length=20)
    logo_url = models.URLField(blank=True, null=True, default=None)
    launch_library_id = models.IntegerField(blank=True, null=True, default=None)
    featured = models.BooleanField(default=False)

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
        if self.launch_library_id:
            return "https://launchlibrary.net/1.3/agency/%s" % self.launch_library_id
        else:
            return None


# The Orbiter object is meant to define spacecraft (past and present) that are human-rated for spaceflight.
#
# Example: Dragon, Orion, etc.
# TODO Add 'in use / capability' fields.
class Orbiter(models.Model):
    name = models.CharField(max_length=200)
    agency = models.CharField(max_length=200, default='Unknown')
    launch_agency = models.ForeignKey(Agency, related_name='orbiter_list', blank=True, null=True)
    history = models.CharField(max_length=1000, default='')
    details = models.CharField(max_length=1000, default='')
    image_url = models.URLField(blank=True)
    nation_url = models.URLField(blank=True)
    wiki_link = models.URLField(blank=True)

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
# TODO Add 'in use / capability' fields.
# TODO Deprecate the 'agency' string field now that its linked to launch_agency.
# TODO Rename back to 'Launcher' now that legacy launcher is deprecated and no longer in use.
class LauncherDetail(models.Model):
    name = models.CharField(max_length=200)
    active = models.BooleanField(default=True)
    description = models.CharField(max_length=2048, default='', blank=True)
    family = models.CharField(max_length=200, default='', blank=True)
    s_family = models.CharField(max_length=200, default='', blank=True)
    agency = models.CharField(max_length=200, default='', blank=True)
    full_name = models.CharField(max_length=200, default='', blank=True)
    launch_agency = models.ForeignKey(Agency, related_name='launcher_list', blank=True, null=True)
    variant = models.CharField(max_length=200, default='', blank=True)
    alias = models.CharField(max_length=200, default='', blank=True)
    min_stage = models.IntegerField(blank=True, null=True)
    max_stage = models.IntegerField(blank=True, null=True)
    length = models.CharField(max_length=200, default='', blank=True)
    diameter = models.CharField(max_length=200, default='', blank=True)
    launch_mass = models.CharField(max_length=200, default='', blank=True)
    leo_capacity = models.CharField(max_length=200, default='', blank=True)
    gto_capacity = models.CharField(max_length=200, default='', blank=True)
    to_thrust = models.CharField(max_length=200, default='', blank=True)
    vehicle_class = models.CharField(max_length=200, default='', blank=True)
    apogee = models.CharField(max_length=200, default='', blank=True)
    vehicle_range = models.CharField(max_length=200, default='', blank=True)
    image_url = models.CharField(max_length=200, default='', blank=True)
    info_url = models.CharField(max_length=200, default='', blank=True)
    wiki_url = models.CharField(max_length=200, default='', blank=True)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        ordering = ['name']
        verbose_name = 'Launcher Detail'
        verbose_name_plural = 'Launcher Details'
