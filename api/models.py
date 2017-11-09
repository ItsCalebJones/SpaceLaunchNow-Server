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
        verbose_name = 'Launcher'
        verbose_name_plural = 'Launchers'


class Orbiter(models.Model):
    name = models.CharField(max_length=200)
    agency = models.CharField(max_length=200, default='Unknown')
    history = models.CharField(max_length=1000, default='')
    details = models.CharField(max_length=1000, default='')
    image_url = models.URLField(blank=True)
    nation_url = models.URLField(blank=True)
    wiki_link = models.URLField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Orbiter'
        verbose_name_plural = 'Orbiters'


class LauncherDetail(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=200, default='')
    family = models.CharField(max_length=200, default='')
    s_family = models.CharField(max_length=200, default='')
    manufacturer = models.CharField(max_length=200, default='')
    variant = models.CharField(max_length=200, default='')
    alias = models.CharField(max_length=200, default='')
    min_stage = models.IntegerField(blank=True, null=True)
    max_stage = models.IntegerField(blank=True, null=True)
    length = models.CharField(max_length=200, default='')
    diameter = models.CharField(max_length=200, default='')
    launch_mass = models.CharField(max_length=200, default='')
    leo_capacity = models.CharField(max_length=200, default='')
    gto_capacity = models.CharField(max_length=200, default='')
    to_thrust = models.CharField(max_length=200, default='')
    vehicle_class = models.CharField(max_length=200, default='')
    apogee = models.CharField(max_length=200, default='')
    vehicle_range = models.CharField(max_length=200, default='')
    image_url = models.CharField(max_length=200, default='')
    info_url = models.CharField(max_length=200, default='')
    wiki_url = models.CharField(max_length=200, default='')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Launcher Detail'
        verbose_name_plural = 'Launcher Details'
