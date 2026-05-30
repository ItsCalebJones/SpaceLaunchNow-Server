from api.models import Article
from django.contrib import admin
from django.utils.html import format_html

from . import models


@admin.register(models.LaunchNotificationRecord)
class LaunchNotificationAdmin(admin.ModelAdmin):
    list_display = (
        "launch_id",
        "last_net_stamp",
        "last_twitter_post",
        "last_notification_sent",
        "last_notification_recipient_count",
        "days_to_launch",
    )
    readonly_fields = ("days_to_launch",)
    ordering = ("last_net_stamp",)
    search_fields = ("launch_id",)


@admin.register(models.Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "message", "send_ios", "send_ios_complete", "send_android", "send_android_complete")
    search_fields = ("title", "message")


@admin.register(models.DailyDigestRecord)
class DailyDigestRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "timestamp", "messages", "count", "data")


@admin.register(models.DiscordChannel)
class DiscordBotAdmin(admin.ModelAdmin):
    list_display = ("name", "channel_id", "server_id")


@admin.register(models.TwitterNotificationChannel)
class TwitterNotificationChannelAdmin(admin.ModelAdmin):
    list_display = ("name", "channel_id", "server_id")


@admin.register(models.TwitterUser)
class TwitterUserAdmin(admin.ModelAdmin):
    list_display = (
        "user_id",
        "screen_name",
        "name",
    )


@admin.register(models.Tweet)
class TweetAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "text", "created_at", "read")


@admin.register(models.SubredditNotificationChannel)
class SubredditNotificationChannelAdmin(admin.ModelAdmin):
    list_display = ("name", "channel_id", "server_id")


@admin.register(models.Subreddit)
class SubredditAdmin(admin.ModelAdmin):
    list_display = ("id", "name")


@admin.register(models.RedditSubmission)
class RedditSubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "text", "link", "read", "created_at")


@admin.register(models.ArticleNotification)
class ArticleNotificationAdmin(admin.ModelAdmin):
    list_display = (
        "article_title",
        "article_news_site",
        "id",
        "created_at",
        "should_notify",
        "was_notified",
        "read",
        "sent_at",
    )
    list_filter = ("should_notify", "was_notified", "read")
    search_fields = ("id",)
    ordering = ("-created_at",)
    readonly_fields = ("article_title", "article_news_site", "article_link")

    def _article(self, obj):
        # ArticleNotification has no FK to Article; its id mirrors Article.id.
        if not hasattr(obj, "_cached_article"):
            obj._cached_article = Article.objects.filter(id=obj.id).first()
        return obj._cached_article

    @admin.display(description="Article")
    def article_title(self, obj):
        article = self._article(obj)
        return article.title if article else "(article not found)"

    @admin.display(description="News Site")
    def article_news_site(self, obj):
        article = self._article(obj)
        return article.news_site if article else "—"

    @admin.display(description="Link")
    def article_link(self, obj):
        article = self._article(obj)
        if article and article.link:
            return format_html('<a href="{}" target="_blank" rel="noopener">{}</a>', article.link, article.link)
        return "—"


@admin.register(models.NewsNotificationChannel)
class NewsNotificationChannelAdmin(admin.ModelAdmin):
    list_display = ("id", "channel_id", "server_id", "name", "subscribed")
