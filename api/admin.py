# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from api.filters.UpcomingFilter import DateListFilter
from . import models


@admin.register(models.LauncherConfig)
class LauncherAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">extension</i>'
    list_display = ('name', 'audited', 'variant', 'full_name', 'family', 'active', 'launch_agency',)
    list_filter = ('name', 'family', 'image_url', 'launch_agency__name', 'audited',)
    ordering = ('name','id')
    search_fields = ('name', 'launch_agency__name')


@admin.register(models.Agency)
class AgencyAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">group</i>'
    list_display = ('short_name', 'featured', 'launchers', 'orbiters', 'short_description')
    list_filter = ('name', 'featured',)
    ordering = ('name',)
    search_fields = ('name',)


@admin.register(models.Orbiter)
class OrbiterAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">public</i>'
    list_display = ('name', 'agency')
    list_filter = ('agency',)
    ordering = ('name',)


@admin.register(models.Launch)
class LaunchAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">launch</i>'
    list_display = ('name', 'net')
    list_filter = (DateListFilter, 'status_name', 'lsp__name', 'launcher_config__name')
    ordering = ('net',)
    search_fields = ('name', 'lsp__name', 'launcher_config__name', 'mission__description')


@admin.register(models.Events)
class EventAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">event</i>'
    list_display = ('name',)
    list_filter = ('name',)


@admin.register(models.Location)
class LocationAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">place</i>'
    list_display = ('name', 'country_code')
    list_filter = ('name', 'country_code')
    ordering = ('name',)


@admin.register(models.Pad)
class PadAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">dashboard</i>'
    list_display = ('name', 'location')
    list_filter = ('name', 'agency_id')
    ordering = ('name',)


@admin.register(models.VidURLs)
class VidAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">video_library</i>'
    list_display = ('vid_url', 'launch')


@admin.register(models.InfoURLs)
class InfoAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">link</i>'
    list_display = ('info_url', 'launch')
