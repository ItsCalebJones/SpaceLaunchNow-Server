# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import apps
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


class EventType(models.Model):
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


class SpacecraftStatus(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        verbose_name = 'Spacecraft Status'
        verbose_name_plural = 'Spacecraft Status\''


class AstronautStatus(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        verbose_name = 'Astronaut Status'
        verbose_name_plural = 'Astronaut Status\''


class AstronautType(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        verbose_name = 'Astronaut Type'
        verbose_name_plural = 'Astronaut Types'


class AstronautRole(models.Model):
    role = models.CharField(max_length=255)

    def __str__(self):
        return self.role

    def __unicode__(self):
        return u'%s' % self.role

    class Meta:
        verbose_name = 'Astronaut Role'
        verbose_name_plural = 'Astronaut Roles'


class SpaceStationStatus(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        verbose_name = 'Space Station Status'
        verbose_name_plural = 'Space Station Status\''


class SpaceStationType(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        verbose_name = 'Space Station Type'
        verbose_name_plural = 'Space Station Types'


class DockingLocation(models.Model):
    name = models.CharField(max_length=255)
    spacestation = models.ForeignKey('api.SpaceStation', on_delete=models.PROTECT, related_name='docking_location', default=4)


    @property
    def docked(self):
        DockingEvent = apps.get_model(app_label='api', model_name='DockingEvent')
        docked = DockingEvent.objects.filter(docking_location=self.id).filter(docked=True).first()
        return docked

    def __str__(self):
        return self.name

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        verbose_name = 'Docking Location'
        verbose_name_plural = 'Docking Locations'


class SpacecraftConfigurationType(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        verbose_name = 'Spacecraft Configuration Type'
        verbose_name_plural = 'Spacecraft Configuration Types'
