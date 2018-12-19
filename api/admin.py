# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.urls import reverse
from django.utils.html import escape

from api.filters.UpcomingFilter import DateListFilter
from api.forms.admin_forms import LaunchForm, LandingForm, LauncherForm, PayloadForm, MissionForm, EventsForm, \
    OrbiterForm, AgencyForm, AstronautForm, SpacecraftFlightForm, SpacecraftForm, LauncherConfigForm, SpaceStationForm
from bot.utils.admin_utils import custom_titled_filter
from . import models


@admin.register(models.LauncherConfig)
class LauncherConfigAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">extension</i>'
    list_display = ('name', 'audited', 'variant', 'full_name', 'family', 'active', 'launch_agency',)
    list_filter = ('name', 'family', 'image_url', 'launch_agency__name', 'audited',)
    ordering = ('name', 'id')
    search_fields = ('name', 'launch_agency__name')
    readonly_fields = ['launch_library_id']
    form = LauncherConfigForm


@admin.register(models.Launcher)
class LauncherAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">extension</i>'
    list_display = ('id', 'serial_number', 'flight_proven', 'status', 'launcher_config')
    list_filter = ('id', 'serial_number', 'flight_proven', 'status', 'launcher_config')
    ordering = ('id', 'serial_number', 'flight_proven', 'status')
    search_fields = ('serial_number', 'launcher_config__name', 'status', 'details')
    form = LauncherForm


@admin.register(models.Mission)
class MissionAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">assignment</i>'
    list_display = ('id', 'name', 'mission_type', 'orbit')
    list_filter = ('id', 'name', 'mission_type', 'orbit')
    readonly_fields = ['launch_library_id']
    ordering = ('id', )
    search_fields = ('name', 'description')
    form = MissionForm


@admin.register(models.Agency)
class AgencyAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">group</i>'
    list_display = ('short_name', 'featured', 'launchers', 'spacecraft', 'short_description')
    list_filter = ('name', 'featured',)
    ordering = ('name',)
    search_fields = ('name',)
    form = AgencyForm


@admin.register(models.Landing)
class LandingAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">group</i>'
    list_display = ('name', 'attempt', 'success', 'landing_location', 'landing_type')
    form = LandingForm

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


class InfoURLs(admin.TabularInline):
    model = models.InfoURLs
    verbose_name = "Information URL"
    verbose_name_plural = "Information URLs"


class VideoURLs(admin.TabularInline):
    model = models.VidURLs
    verbose_name = "Video URL"
    verbose_name_plural = "Videos URLs"


class FirstStageInline(admin.TabularInline):
    model = models.FirstStage
    verbose_name = "Launcher Stage"
    verbose_name_plural = "Launcher Stages"


class DockingEventInline(admin.StackedInline):
    model = models.DockingEvent
    verbose_name = "Docking Event"
    verbose_name_plural = "Docking Events"


class SpacecraftFlightInline(admin.StackedInline):
    model = models.SpacecraftFlight
    verbose_name = "Spacecraft Stage"
    verbose_name_plural = "Spacecraft Stage"

class SpacecraftFlightInlineForSpacecraft(admin.StackedInline):
    model = models.SpacecraftFlight
    verbose_name = "Flight"
    verbose_name_plural = "Flights"


@admin.register(models.Rocket)
class RocketAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">group</i>'
    list_display = ('id', 'launch',)
    search_fields = ('launch__name',)
    inlines = [FirstStageInline, SpacecraftFlightInline]


@admin.register(models.FirstStage)
class FirstStageAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">group</i>'
    list_display = ('id', 'landing', 'launcher', 'rocket')


@admin.register(models.SecondStage)
class SecondStageAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">group</i>'
    list_display = ('id', 'landing', 'launcher', 'rocket')


@admin.register(models.SpacecraftConfiguration)
class OrbiterConfigurationAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">public</i>'
    list_display = ('name', 'agency')
    list_filter = ('agency',)
    ordering = ('name',)
    form = OrbiterForm


@admin.register(models.Launch)
class LaunchAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">launch</i>'
    list_display = ('name', 'net', 'rocket', 'mission', 'orbit')
    list_filter = (DateListFilter,  ('status__name', custom_titled_filter('Launch Status')),
                   ('rocket__configuration__launch_agency__name', custom_titled_filter('LSP Name')),
                   ('rocket__configuration__name', custom_titled_filter('Launch Configuration Name')))
    ordering = ('net',)
    search_fields = ('name', 'rocket__configuration__launch_agency__name', 'mission__description')
    readonly_fields = ['slug', 'launch_library_id', 'launch_library']
    form = LaunchForm
    inlines = [InfoURLs, VideoURLs]

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
    form = EventsForm


@admin.register(models.Location)
class LocationAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">place</i>'
    list_display = ('name', 'country_code')
    list_filter = ('name', 'country_code')
    readonly_fields = ['launch_library_id']
    ordering = ('name',)


@admin.register(models.Pad)
class PadAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">dashboard</i>'
    list_display = ('name', 'location')
    list_filter = ('name', 'agency_id')
    readonly_fields = ['launch_library_id']
    ordering = ('name',)


@admin.register(models.Payload)
class PayloadAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">dashboard</i>'
    list_display = ('name', 'mission')
    list_filter = ('name', 'mission')
    ordering = ('name',)
    form = PayloadForm


@admin.register(models.VidURLs)
class VidAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">video_library</i>'
    list_display = ('vid_url', 'launch')


@admin.register(models.InfoURLs)
class InfoAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">link</i>'
    list_display = ('info_url', 'launch')


@admin.register(models.Astronauts)
class AstronautsAdmin(admin.ModelAdmin):
    list_display = ('name', 'nationality', 'status', 'agency')
    list_filter = ('name', 'nationality', 'status', 'agency')
    search_fields = ('name', 'agency__name')
    readonly_fields = ["slug"]
    form = AstronautForm


@admin.register(models.AstronautFlight)
class AstronautFlightAdmin(admin.ModelAdmin):
    list_display = ('id', 'astronaut', 'role')


class ExpeditionInline(admin.StackedInline):
    model = models.Expedition
    verbose_name = "Expedition"
    verbose_name_plural = "Expeditions"


@admin.register(models.DockingEvent)
class DockingEventAdmin(admin.ModelAdmin):
    list_display = ('space_station', 'flight_vehicle')


@admin.register(models.SpaceStation)
class SpaceStationAdmin(admin.ModelAdmin):
    list_display = ('name', )
    form = SpaceStationForm
    inlines = [ExpeditionInline, ]


@admin.register(models.SpacecraftFlight)
class SpacecraftFlightAdmin(admin.ModelAdmin):
    list_display = ('spacecraft_name', )
    list_filter = ('spacecraft__spacecraft_config', 'spacecraft__status',
                   'rocket__configuration__launch_agency__name')
    search_fields = ('spacecraft__name', 'rocket__name', 'rocket__launch_name')
    inlines = [DockingEventInline,]

    def spacecraft_name(self, obj):
        return obj.spacecraft.name + " | " + obj.rocket.launch.name


@admin.register(models.Spacecraft)
class SpacecraftAdmin(admin.ModelAdmin):
    list_display = ('name', 'serial_number', 'status', 'flights')
    list_filter = ('status', 'spacecraft_config',)
    form = SpacecraftForm
    read_only_fields = ('flights',)
    search_fields = ('name', 'spacecraft_config__name')
    inlines = [SpacecraftFlightInlineForSpacecraft, ]

    def status(self, obj):
        return obj.status.name

    def flights(self, obj):
        return '<a href="/admin/api/spacecraftflight/?spacecraft__spacecraft_config__id__exact=%d">%s Flights</a>' % (obj.spacecraft_config.id, obj.name)

    flights.allow_tags = True
