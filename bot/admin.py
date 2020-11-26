# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from . import models


@admin.register(models.LaunchNotificationRecord)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('launch_id', 'last_net_stamp', 'last_twitter_post', 'last_notification_sent',
                    'last_notification_recipient_count', 'days_to_launch')
    readonly_fields = ('days_to_launch',)
    ordering = ('last_net_stamp',)
    search_fields = ('launch_id',)


@admin.register(models.Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'message', 'send_ios', 'send_ios_complete',
                    'send_android', 'send_android_complete')
    search_fields = ('title', 'message')


@admin.register(models.DailyDigestRecord)
class DailyDigestRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'timestamp', 'messages', 'count', 'data')


@admin.register(models.DiscordChannel)
class DiscordBotAdmin(admin.ModelAdmin):
    list_display = ('name', 'channel_id', 'server_id')


@admin.register(models.TwitterNotificationChannel)
class TwitterNotificationChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'channel_id', 'server_id')


@admin.register(models.TwitterUser)
class TwitterUserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'screen_name', 'name',)


@admin.register(models.Tweet)
class TweetAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'text', 'created_at', 'read')


@admin.register(models.SubredditNotificationChannel)
class SubredditNotificationChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'channel_id', 'server_id')


@admin.register(models.Subreddit)
class SubredditAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(models.RedditSubmission)
class RedditSubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'text', 'link', 'read', 'created_at')


@admin.register(models.ArticleNotification)
class ArticleNotification(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'article')


@admin.register(models.NewsNotificationChannel)
class NewsNotificationChannelAdmin(admin.ModelAdmin):
    list_display = ('id', 'channel_id', 'server_id', 'name', 'subscribed')
