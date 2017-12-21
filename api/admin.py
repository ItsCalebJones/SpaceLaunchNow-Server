# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from . import models


@admin.register(models.LauncherDetail)
class LauncherDetailAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">account_balance</i>'
    list_display = ('name', 'active',  'variant', 'family', 'full_name',   'agency', 'launch_agency', 'leo_capacity', 'gto_capacity')
    list_filter = ('family', 'agency',)


@admin.register(models.Agency)
class AgencyAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">account_balance</i>'
    list_display = ('agency', 'launchers', 'orbiters', 'description')
    list_filter = ('agency',)


@admin.register(models.Launcher)
class LauncherAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">account_balance</i>'
    list_display = ('name', 'agency')
    list_filter = ('agency',)


@admin.register(models.Orbiter)
class OrbiterAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">account_balance</i>'
    list_display = ('name', 'agency')
    list_filter = ('agency',)