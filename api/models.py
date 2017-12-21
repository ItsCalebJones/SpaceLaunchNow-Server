# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


# Create your models here.
class Launcher(models.Model):
    name = models.CharField(max_length=200)
    agency = models.CharField(max_length=200, default='Unknown')
    image_url = models.URLField(blank=True)
    nation_url = models.URLField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Launcher (Legacy)'
        verbose_name_plural = 'Launchers (Legacy)'


# Create your models here.
class Agency(models.Model):
    agency = models.CharField(max_length=200, primary_key=True)
    description = models.CharField(max_length=2048, default='')
    launchers = models.CharField(max_length=500, default='', blank=True)
    orbiters = models.CharField(max_length=500, default='', blank=True)
    image_url = models.URLField(blank=True)
    nation_url = models.URLField(blank=True)

    def __str__(self):
        return self.agency

    class Meta:
        verbose_name = 'Agency'
        verbose_name_plural = 'Agencies'


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
        return '%s' % self.name

    class Meta:
        verbose_name = 'Orbiter'
        verbose_name_plural = 'Orbiters'


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
        return '%s' % self.name

    class Meta:
        verbose_name = 'Launcher Detail'
        verbose_name_plural = 'Launcher Details'
