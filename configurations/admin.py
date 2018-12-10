# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from configurations import models


@admin.register(models.MissionType)
class MissionTypeAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">assessment</i>'
    list_display = ('id', 'name',)
    list_filter = ('id', 'name',)
    ordering = ('id', )
    search_fields = ('name',)


@admin.register(models.AgencyType)
class AgencyTypeAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">group</i>'
    list_display = ('id', 'name',)
    list_filter = ('id', 'name',)
    ordering = ('id', )
    search_fields = ('name',)


@admin.register(models.LaunchStatus)
class LaunchStatusAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">launch</i>'
    list_display = ('id', 'name',)
    list_filter = ('id', 'name',)
    ordering = ('id', )
    search_fields = ('name',)


@admin.register(models.FirstStageType)
class FirstStageTypeAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">launch</i>'
    list_display = ('id', 'name',)
    list_filter = ('id', 'name',)
    ordering = ('id', )
    search_fields = ('name',)


@admin.register(models.Orbit)
class OrbitAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">extension</i>'
    list_display = ('name', 'abbrev',)
    list_filter = ('name', 'abbrev',)
    ordering = ('name', 'abbrev',)
    search_fields = ('name',)


@admin.register(models.LandingLocation)
class LandingLocationAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">place</i>'
    list_display = ('name', )
    list_filter = ('name', )
    ordering = ('name', )
    search_fields = ('name',)


@admin.register(models.LandingType)
class LandingTypeAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">dashboard</i>'
    list_display = ('name',)
    list_filter = ('name', )
    ordering = ('name', )
    search_fields = ('name',)


@admin.register(models.SpaceStationStatus)
class SpaceStationStatusAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(models.AstronautStatus)
class AstronautStatusAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(models.SpacecraftStatus)
class SpacecraftStatusAdmin(admin.ModelAdmin):
    list_display = ('name', )


@admin.register(models.AstronautRole)
class AstronautRoleAdmin(admin.ModelAdmin):
    list_display = ('role', )
