from django.db import models
from django.db.models.functions import datetime
from pytz import utc

from api.models import Launch


class Notification(models.Model):
    launch = models.OneToOneField(Launch, on_delete=models.CASCADE)

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

    def __unicode__(self):
        return self.launch.name

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
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'


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


class TwitterUser(models.Model):
    user_id = models.BigIntegerField( null=False, primary_key=True)
    screen_name = models.CharField(max_length=50, null=False)
    name = models.CharField(max_length=50, null=False)
    profile_image = models.CharField(max_length=50, null=False)
    subscribers = models.ManyToManyField(DiscordChannel)


class Tweet(models.Model):
    id = models.BigIntegerField(primary_key=True)
    user = models.ForeignKey(TwitterUser, related_name='tweets')
    text = models.CharField(max_length=280, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
