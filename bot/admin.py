# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from . import models


@admin.register(models.Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('launch', 'last_net_stamp', 'last_twitter_post', 'last_notification_sent',
                    'last_notification_recipient_count', 'days_to_launch')
    readonly_fields = ('days_to_launch',)


@admin.register(models.DailyDigestRecord)
class DailyDigestRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'timestamp', 'messages', 'count', 'data')