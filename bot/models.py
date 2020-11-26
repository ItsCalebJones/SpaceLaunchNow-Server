import uuid
from django.db import models
from django.db.models.functions import datetime
from pytz import utc

from api.models import Launch, Events, Article


class LaunchNotificationRecord(models.Model):
    launch_id = models.UUIDField(default=uuid.uuid4, editable=False, blank=False, null=False)

    wasNotifiedWebcastLive = models.BooleanField(blank=True, default=False)
    wasNotifiedTwentyFourHour = models.BooleanField(blank=True, default=False)
    wasNotifiedOneHour = models.BooleanField(blank=True, default=False)
    wasNotifiedTenMinutes = models.BooleanField(blank=True, default=False)
    wasNotifiedOneMinute = models.BooleanField(blank=True, default=False)
    wasNotifiedInFlight = models.BooleanField(blank=True, default=False)
    wasNotifiedSuccess = models.BooleanField(blank=True, default=False)

    wasNotifiedTwentyFourHourTwitter = models.BooleanField(blank=True, default=False)
    wasNotifiedOneHourTwitter = models.BooleanField(blank=True, default=False)
    wasNotifiedTenMinutesTwitter = models.BooleanField(blank=True, default=False)
    wasNotifiedOneMinuteTwitter = models.BooleanField(blank=True, default=False)
    wasNotifiedInFlightTwitter = models.BooleanField(blank=True, default=False)
    wasNotifiedSuccessTwitter = models.BooleanField(blank=True, default=False)
    wasNotifiedWebcastLiveTwitter = models.BooleanField(blank=True, default=False)

    wasNotifiedDailyDigest = models.BooleanField(blank=True, default=False)

    last_twitter_post = models.DateTimeField(blank=True, null=True)
    last_notification_sent = models.DateTimeField(blank=True, null=True)
    last_notification_recipient_count = models.IntegerField(blank=True, null=True)
    last_net_stamp = models.DateTimeField(blank=True, null=True)
    last_net_stamp_timestamp = models.DateTimeField(blank=True, null=True)

    wasNotifiedTwentyFourHourDiscord = models.BooleanField(blank=True, default=False)
    wasNotifiedOneHourDiscord = models.BooleanField(blank=True, default=False)
    wasNotifiedTenMinutesDiscord = models.BooleanField(blank=True, default=False)
    wasNotifiedOneMinutesDiscord = models.BooleanField(blank=True, default=False)
    wasNotifiedInFlightDiscord = models.BooleanField(blank=True, default=False)
    wasNotifiedSuccessDiscord = models.BooleanField(blank=True, default=False)
    wasNotifiedWebcastDiscord = models.BooleanField(blank=True, default=False)

    def __unicode__(self):
        return str(self.launch_id)

    def __str__(self):
        return str(self.launch_id)

    def days_to_launch(self):
        if self.last_net_stamp:
            now = datetime.datetime.now(tz=utc)
            diff = self.last_net_stamp - now
            return diff.days

    def is_future(self):
        if self.last_net_stamp is not None or 0:
            now = datetime.datetime.now(tz=utc)
            diff = self.last_net_stamp - now
            if diff.total_seconds() > 0:
                return True
        return False
    is_future.boolean = True

    class Meta:
        verbose_name = 'Notification Record'
        verbose_name_plural = 'Notification Records'


class DailyDigestRecord(models.Model):
    id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField(blank=True, null=True)
    messages = models.TextField(max_length=1048, blank=True, null=True)
    count = models.IntegerField(null=True)
    data = models.TextField(max_length=4096, blank=True, null=True)

    def __unicode__(self):
        return self.id

    class Meta:
        verbose_name = 'Daily Digest - Record'
        verbose_name_plural = 'Daily Digest - Records'


class DiscordChannel(models.Model):
    channel_id = models.CharField(max_length=4000, unique=True)
    server_id = models.CharField(max_length=4000, unique=False)
    name = models.CharField(max_length=4000)

    def __str__(self):
        return '{} ({})'.format(self.name, self.channel_id)

    class Meta:
        verbose_name = "Channel"
        verbose_name_plural = "Channels"


class TwitterNotificationChannel(models.Model):
    id = models.AutoField(primary_key=True)
    channel_id = models.CharField(max_length=4000, unique=True)
    server_id = models.CharField(max_length=4000, unique=False)
    name = models.CharField(max_length=4000)
    default_subscribed = models.BooleanField(default=False)

    def __str__(self):
        return '{} ({})'.format(self.name, self.channel_id)

    class Meta:
        verbose_name = "Twitter Notification Channel"
        verbose_name_plural = "Twitter Notification Channels"


class TwitterUser(models.Model):
    user_id = models.BigIntegerField(null=False, primary_key=True)
    screen_name = models.CharField(max_length=255, null=False)
    name = models.CharField(max_length=255, null=False)
    profile_image = models.CharField(max_length=1048, null=False)
    subscribers = models.ManyToManyField(TwitterNotificationChannel)
    custom = models.BooleanField(default=False)
    default = models.BooleanField(default=False)

    def __str__(self):
        return self.screen_name


class Tweet(models.Model):
    id = models.BigIntegerField(primary_key=True)
    user = models.ForeignKey(TwitterUser, related_name='tweets', on_delete=models.CASCADE)
    text = models.CharField(max_length=1048, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    default = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)


class SubredditNotificationChannel(models.Model):
    id = models.AutoField(primary_key=True)
    channel_id = models.CharField(max_length=4000, unique=True)
    server_id = models.CharField(max_length=4000, unique=False)
    name = models.CharField(max_length=4000)

    def __str__(self):
        return '{} ({})'.format(self.name, self.channel_id)

    class Meta:
        verbose_name = "Reddit Notification Channel"
        verbose_name_plural = "Reddit Notification Channels"


class Subreddit(models.Model):
    id = models.CharField(primary_key=True, max_length=255)
    name = models.CharField(max_length=1048, null=False)
    initialized = models.BooleanField(default=False)
    subscribers = models.ManyToManyField(SubredditNotificationChannel)

    def __str__(self):
        return self.name


class RedditSubmission(models.Model):
    id = models.CharField(primary_key=True, max_length=255)
    subreddit = models.ForeignKey(Subreddit, related_name='submissions', on_delete=models.CASCADE)
    user = models.CharField(max_length=255, null=False)
    selftext = models.BooleanField(default=False)
    score = models.IntegerField(default=0)
    comments = models.IntegerField(default=0)
    title = models.CharField(max_length=1048, null=True, blank=True, default="")
    thumbnail = models.CharField(max_length=1048, null=True, blank=True, default="")
    text = models.CharField(max_length=40000, null=True, blank=True, default="")
    link = models.CharField(max_length=1048, null=True, blank=True, default="")
    permalink = models.CharField(max_length=1048, null=False)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.id


class NewsNotificationChannel(models.Model):
    id = models.AutoField(primary_key=True)
    channel_id = models.CharField(max_length=4000, unique=True)
    server_id = models.CharField(max_length=4000, unique=False)
    name = models.CharField(max_length=4000)
    subscribed = models.BooleanField(default=False)

    def __str__(self):
        return '{} ({})'.format(self.name, self.channel_id)

    class Meta:
        verbose_name = "News Notification Channel"
        verbose_name_plural = "News Notification Channels"


class ArticleNotification(models.Model):
    id = models.CharField(primary_key=True, max_length=255)
    article = models.OneToOneField(Article, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    should_notify = models.BooleanField(default=False)
    was_notified = models.BooleanField(default=False)

    def __str__(self):
        return self.article.title


class Notification(models.Model):
    launch = models.ForeignKey(Launch, on_delete=models.CASCADE, null=True, blank=True, default=None)
    news = models.ForeignKey(Article, on_delete=models.CASCADE, null=True, blank=True, default=None)
    event = models.ForeignKey(Events, on_delete=models.CASCADE, null=True, blank=True, default=None)
    title = models.TextField(max_length=32)
    message = models.TextField(max_length=300)
    send_ios = models.BooleanField(default=False)
    send_ios_complete = models.NullBooleanField(default=False)
    send_android = models.BooleanField(default=False)
    send_android_complete = models.NullBooleanField(default=False)
