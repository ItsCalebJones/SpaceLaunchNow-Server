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

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = 'Launch Status'
        verbose_name_plural = 'Launch Statuses'


class Orbit(models.Model):
    name = models.CharField(primary_key=True, editable=True, max_length=30)
    abbrev = models.CharField(max_length=30)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name', ]
        verbose_name = 'Orbit'
        verbose_name_plural = 'Orbits'


class MissionType(models.Model):
    id = models.IntegerField(primary_key=True, editable=True)
    name = models.CharField(max_length=255, blank=True, default="")

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name


class FirstStageType(models.Model):
    id = models.IntegerField(primary_key=True, editable=True)
    name = models.CharField(max_length=50, blank=True, default="")

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name


class LandingType(models.Model):
    id = models.AutoField(primary_key=True, editable=True)
    name = models.CharField(max_length=255, blank=True, default="")
    abbrev = models.CharField(max_length=255, blank=True, default="")
    description = models.CharField(max_length=2048, null=True, blank=True)

    def __str__(self):
        return "%s (%s)" % (self.name, self.abbrev)

    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.abbrev)


class LandingLocation(models.Model):
    id = models.AutoField(primary_key=True, editable=True)
    name = models.CharField(max_length=255, blank=True, default="")
    abbrev = models.CharField(max_length=255, blank=True, default="")
    description = models.CharField(max_length=2048, null=True, blank=True)

    def __str__(self):
        return "%s (%s)" % (self.name, self.abbrev)

    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.abbrev)


class OrbiterStatus(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        verbose_name = 'Orbiter Status'
        verbose_name_plural = 'Orbiter Status\''


class AstronautStatus(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        verbose_name = 'Astronaut Status'
        verbose_name_plural = 'Astronaut Status\''


class SpaceStationStatus(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        verbose_name = 'Space Station Status'
        verbose_name_plural = 'Space Station Status\''
