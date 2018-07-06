# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from . import models


@admin.register(models.Launcher)
class LauncherDetailAdmin(admin.ModelAdmin):
    list_display = ('name', 'active',  'variant', 'family', 'full_name', 'launch_agency', 'leo_capacity',
                    'gto_capacity')
    list_filter = ('family', 'agency',)


@admin.register(models.Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = ('short_name', 'featured', 'launchers', 'orbiters', 'short_description')
    list_filter = ('name', 'featured',)


@admin.register(models.Orbiter)
class OrbiterAdmin(admin.ModelAdmin):
    list_display = ('name', 'agency')
    list_filter = ('agency',)


@admin.register(models.Launch)
class LaunchAdmin(admin.ModelAdmin):
    list_display = ('name', 'net')
    list_filter = ('name',)


@admin.register(models.Events)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name',)
    list_filter = ('name',)