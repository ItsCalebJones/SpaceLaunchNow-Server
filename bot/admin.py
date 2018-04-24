# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from . import models


@admin.register(models.Launch)
class LaunchAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'status', 'inhold', 'net')
    list_select_related = True


@admin.register(models.Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'country_code', 'show_launches')
    list_select_related = True

    def show_launches(self, obj):
        return "\n".join([a.name for a in obj.launches.all()])
    show_launches.short_description = 'Launches'

@admin.register(models.Pad)
class PadAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'location')
    list_select_related = True


@admin.register(models.Rocket)
class RocketAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'configuration', 'show_launches')

    def show_launches(self, obj):
        return "\n".join([a.name for a in obj.launches.all()])
    show_launches.short_description = 'Launches'


@admin.register(models.Agency)
class AgencyAdmin(admin.ModelAdmin):
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
    list_display = ('id', 'name', 'type_name', 'launch')


@admin.register(models.Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('launch', 'last_net_stamp', 'last_twitter_post', 'last_notification_sent',
                    'last_notification_recipient_count', 'days_to_launch')
    readonly_fields = ('days_to_launch',)


@admin.register(models.DailyDigestRecord)
class DailyDigestRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'timestamp', 'messages', 'count', 'data')