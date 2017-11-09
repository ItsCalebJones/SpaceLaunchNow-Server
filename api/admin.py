# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from . import models


@admin.register(models.LauncherDetail)
class LauncherDetailAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">account_balance</i>'
    list_display = ('name',  'variant', 'family', 's_family', 'manufacturer', 'min_stage', 'max_stage')
    list_filter = ('family', 'manufacturer',)

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