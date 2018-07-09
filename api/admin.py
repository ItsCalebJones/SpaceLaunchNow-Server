# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime
from django.contrib import admin
from django.shortcuts import redirect

from . import models


@admin.register(models.Launcher)
class LauncherDetailAdmin(admin.ModelAdmin):
    list_display = ('name', 'active',  'variant', 'family', 'full_name', 'launch_agency', 'leo_capacity',
                    'gto_capacity')
    list_filter = ('family', 'agency', 'image_url')
    ordering = ('name',)
    search_fields = ('name', 'agency__name',)


@admin.register(models.Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = ('short_name', 'featured', 'launchers', 'orbiters', 'short_description')
    list_filter = ('name', 'featured',)
    ordering = ('name',)


@admin.register(models.Orbiter)
class OrbiterAdmin(admin.ModelAdmin):
    list_display = ('name', 'agency')
    list_filter = ('agency',)
    ordering = ('name',)


@admin.register(models.Launch)
class LaunchAdmin(admin.ModelAdmin):
    list_display = ('name', 'net')
    list_filter = ('net', 'status_name', 'lsp__name', 'launcher__name')
    ordering = ('net',)
    search_fields = ('name', 'lsp__name', 'launcher__name', 'mission__description')


@admin.register(models.Events)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name',)
    list_filter = ('name',)


@admin.register(models.Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'country_code')
    list_filter = ('name', 'country_code')
    ordering = ('name',)


@admin.register(models.Pad)
class PadAdmin(admin.ModelAdmin):
    list_display = ('name', 'location')
    list_filter = ('name', 'agency_id')
    ordering = ('name',)