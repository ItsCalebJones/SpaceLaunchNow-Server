# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from . import models


@admin.register(models.Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('launch', 'last_net_stamp', 'last_twitter_post', 'last_notification_sent',
                    'last_notification_recipient_count', 'days_to_launch')
    readonly_fields = ('days_to_launch',)
    ordering = ('launch__net',)
    search_fields = ('launch__name',)


@admin.register(models.DailyDigestRecord)
class DailyDigestRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'timestamp', 'messages', 'count', 'data')


@admin.register(models.DiscordChannel)
class DiscordBotAdmin(admin.ModelAdmin):
    list_display = ('name', 'channel_id', 'server_id')


@admin.register(models.TwitterNotificationChannel)
class TwitterNotificationChannel(admin.ModelAdmin):
    list_display = ('name', 'channel_id', 'server_id')


@admin.register(models.TwitterUser)
class TwitterUserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'screen_name', 'name',)


@admin.register(models.Tweet)
class TweetAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'text', 'created_at', 'read')