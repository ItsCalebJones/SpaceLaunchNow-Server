from django.db import models
from django.db.models.functions import datetime
from pytz import utc

from api.models import Launch


class Notification(models.Model):
    launch = models.OneToOneField(Launch, on_delete=models.CASCADE)
    wasNotifiedTwentyFourHour = models.BooleanField(blank=True, default=False)
    wasNotifiedOneHour = models.BooleanField(blank=True, default=False)
    wasNotifiedTenMinutes = models.BooleanField(blank=True, default=False)
    wasNotifiedTwentyFourHourTwitter = models.BooleanField(blank=True, default=False)
    wasNotifiedOneHourTwitter = models.BooleanField(blank=True, default=False)
    wasNotifiedTenMinutesTwitter = models.BooleanField(blank=True, default=False)
    wasNotifiedDailyDigest = models.BooleanField(blank=True, default=False)
    last_twitter_post = models.DateTimeField(blank=True, null=True)
    last_notification_sent = models.DateTimeField(blank=True, null=True)
    last_notification_recipient_count = models.IntegerField(blank=True, null=True)
    last_net_stamp = models.IntegerField(blank=True, null=True)
    last_net_stamp_timestamp = models.DateTimeField(blank=True, null=True)

    def __unicode__(self):
        return self.launch.name

    def days_to_launch(self):
        if self.last_net_stamp:
            now = datetime.datetime.utcnow().replace(tzinfo=utc)
            diff = datetime.datetime.fromtimestamp(self.last_net_stamp, tz=utc) - now
            return diff.days

    def is_future(self):
        if self.last_net_stamp is not None or 0:
            now = datetime.datetime.utcnow().replace(tzinfo=utc)
            diff = datetime.datetime.fromtimestamp(self.last_net_stamp, tz=utc) - now
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