# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from api.filters.UpcomingFilter import DateListFilter
from bot.utils.admin_utils import custom_titled_filter
from . import models


@admin.register(models.LauncherConfig)
class LauncherConfigAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">extension</i>'
    list_display = ('name', 'audited', 'variant', 'full_name', 'family', 'active', 'launch_agency',)
    list_filter = ('name', 'family', 'image_url', 'launch_agency__name', 'audited',)
    ordering = ('name', 'id')
    search_fields = ('name', 'launch_agency__name')


@admin.register(models.Launcher)
class LauncherAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">extension</i>'
    list_display = ('id', 'serial_number', 'flight_proven', 'status', 'launcher_config')
    list_filter = ('id', 'serial_number', 'flight_proven', 'status', 'launcher_config')
    ordering = ('id', 'serial_number', 'flight_proven', 'status')
    search_fields = ('serial_number', 'launcher_config', 'status', 'details')


@admin.register(models.Mission)
class MissionAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">assignment</i>'
    list_display = ('id', 'name', 'mission_type', 'orbit')
    list_filter = ('id', 'name', 'mission_type', 'orbit')
    ordering = ('id', )
    search_fields = ('name', 'description')


@admin.register(models.Agency)
class AgencyAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">group</i>'
    list_display = ('short_name', 'featured', 'launchers', 'orbiters', 'short_description')
    list_filter = ('name', 'featured',)
    ordering = ('name',)
    search_fields = ('name',)


@admin.register(models.Landing)
class LandingAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">group</i>'
    list_display = ('name', 'attempt', 'success', 'landing_location', 'landing_type')

    def name(self, obj):
        try:
            if obj.firststage is not None:
                return u"Landing: %s" % obj.firststage
            elif obj.secondstage is not None:
                return u"Landing: %s" % obj.secondstage
            else:
                return u"(%d) Unassigned Landing" % obj.id
        except (models.Launch.DoesNotExist, models.FirstStage.DoesNotExist) as e:
            return u"(%d) Unassigned Landing" % obj.id


class FirstStageInline(admin.TabularInline):
    model = models.FirstStage


class SecondStageInline(admin.TabularInline):
    model = models.SecondStage


@admin.register(models.Rocket)
class RocketAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">group</i>'
    list_display = ('id', 'launch',)
    search_fields = ('launch__name',)
    inlines = [FirstStageInline, SecondStageInline]


@admin.register(models.FirstStage)
class FirstStageAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">group</i>'
    list_display = ('id', 'landing', 'launcher', 'rocket')


@admin.register(models.SecondStage)
class SecondStageAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">group</i>'
    list_display = ('id', 'landing', 'launcher', 'rocket')


@admin.register(models.Orbiter)
class OrbiterAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">public</i>'
    list_display = ('name', 'agency')
    list_filter = ('agency',)
    ordering = ('name',)


@admin.register(models.Launch)
class LaunchAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">launch</i>'
    list_display = ('name', 'net', 'rocket', 'mission', 'orbit')
    list_filter = (DateListFilter,  ('launch_status__name', custom_titled_filter('Launch Status')),
                   ('rocket__configuration__launch_agency__name', custom_titled_filter('LSP Name')),
                   ('rocket__configuration__name', custom_titled_filter('Launch Configuration Name')))
    ordering = ('net',)
    search_fields = ('name', 'rocket__configuration__launch_agency__name', 'mission__description')

    def orbit(self, obj):
        if obj.mission is not None and obj.mission.orbit is not None and obj.mission.orbit.name:
            return obj.mission.orbit.name
        else:
            return None

    orbit.short_description = 'Orbit'


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
