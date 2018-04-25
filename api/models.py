# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


# The Agency object is meant to define a agency that operates launchers and orbiters.
#
# Example: SpaceX has Falcon 9 Launchers and Dragon orbiters
#
class Agency(models.Model):
    agency = models.CharField(max_length=200, primary_key=True)
    description = models.CharField(max_length=2048, default='', blank=True)
    launchers = models.CharField(max_length=500, default='', blank=True)
    orbiters = models.CharField(max_length=500, default='', blank=True)
    image_url = models.URLField(blank=True)
    nation_url = models.URLField(blank=True)
    ceo = models.CharField(max_length=200, blank=True)
    founding_year = models.CharField(blank=True, default='', max_length=20)
    logo_url = models.URLField(blank=True)
    launch_library_id = models.IntegerField(blank=True, null=True, default=None)
    featured = models.BooleanField(default=False)

    def __str__(self):
        return self.agency

    def __unicode__(self):
        return u'%s' % self.agency

    class Meta:
        ordering = ['agency']
        verbose_name = 'Agency'
        verbose_name_plural = 'Agencies'


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
