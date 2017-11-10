# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from . import models

@admin.register(models.Launch)
class LaunchAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">view_agenda</i>'
    list_display = ('id', 'name', 'status', 'inhold', 'net')
    list_select_related = True


@admin.register(models.Location)
class LocationAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">location_on</i>'
    list_display = ('id', 'name', 'country_code', 'show_launches')
    list_select_related = True

    def show_launches(self, obj):
        return "\n".join([a.name for a in obj.launches.all()])
    show_launches.short_description = 'Launches'

@admin.register(models.Pad)
class PadAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">my_location</i>'
    list_display = ('id', 'name', 'location')
    list_select_related = True


@admin.register(models.Rocket)
class RocketAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">navigation</i>'
    list_display = ('id', 'name', 'configuration', 'show_launches')

    def show_launches(self, obj):
        return "\n".join([a.name for a in obj.launches.all()])
    show_launches.short_description = 'Launches'


@admin.register(models.Agency)
class AgencyAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">business</i>'
    list_display = ('id', 'name', 'type', 'show_pads', 'show_locations', 'show_rockets')

    def show_pads(self, obj):
        return "\n".join([a.name for a in obj.pads.all()])
    show_pads.short_description = 'Pads'

    def show_locations(self, obj):
        return "\n".join([a.name for a in obj.locations.all()])
    show_locations.short_description = 'Locations'

    def show_rockets(self, obj):
        return "\n".join([a.name for a in obj.rockets.all()])
    show_rockets.short_description = 'Rockets'

@admin.register(models.Mission)
class MissionAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">assignment</i>'
    list_display = ('id', 'name', 'type_name', 'launch')