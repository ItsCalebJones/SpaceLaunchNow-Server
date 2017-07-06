from django.db import models


class Launch(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    status = models.IntegerField(blank=True)
    netstamp = models.IntegerField(blank=True, null=True)
    wsstamp = models.IntegerField(blank=True, null=True)
    westamp = models.IntegerField(blank=True, null=True)
    inhold = models.IntegerField(blank=True, null=True)
    rocket_name = models.CharField(max_length=255, blank=True, default="")
    mission_name = models.CharField(max_length=255, blank=True, default="")
    location_name = models.CharField(max_length=255, blank=True, default="")


class Notification(models.Model):
    launch = models.OneToOneField(Launch, on_delete=models.CASCADE)
    wasNotifiedTwentyFourHour = models.BooleanField(blank=True, default=False)
    wasNotifiedOneHour = models.BooleanField(blank=True, default=False)
    wasNotifiedTenMinutes = models.BooleanField(blank=True, default=False)
    wasNotifiedDailyDigest = models.BooleanField(blank=True, default=False)
    last_twitter_post = models.DateTimeField(blank=True, null=True)
    last_net_stamp = models.IntegerField(blank=True, null=True)
    last_net_stamp_timestamp = models.DateTimeField(blank=True, null=True)


class DailyDigestRecord(models.Model):
    id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField(blank=True, null=True)
    messages = models.TextField(max_length=1048, blank=True, null=True)
    count = models.IntegerField(null=True)
    data = models.TextField(max_length=4096, blank=True, null=True)

