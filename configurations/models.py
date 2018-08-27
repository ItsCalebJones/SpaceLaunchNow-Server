# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class AgencyType(models.Model):
    id = models.IntegerField(primary_key=True, editable=True)
    name = models.CharField(max_length=255, blank=True, default="")

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name


class LaunchStatus(models.Model):
    id = models.IntegerField(primary_key=True, editable=True)
    name = models.CharField(max_length=255, blank=True, default="")

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = 'Launch Status'
        verbose_name_plural = 'Launch Statuses'


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


class LandingType(models.Model):
    id = models.IntegerField(primary_key=True, editable=True)
    name = models.CharField(max_length=255, blank=True, default="")
    description = models.CharField(max_length=2048, null=True, blank=True)

    def __unicode__(self):
        return self.name


class LandingLocation(models.Model):
    id = models.IntegerField(primary_key=True, editable=True)
    name = models.CharField(max_length=255, blank=True, default="")

    def __unicode__(self):
        return self.name