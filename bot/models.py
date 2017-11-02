from django.db import models


class Launch(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    img_url = models.CharField(max_length=255, blank=True, null=True)
    status = models.IntegerField(blank=True)
    netstamp = models.IntegerField(blank=True, null=True)
    wsstamp = models.IntegerField(blank=True, null=True)
    westamp = models.IntegerField(blank=True, null=True)
    inhold = models.IntegerField(blank=True, null=True)
    net = models.CharField(max_length=255, null=True)
    window_end = models.CharField(max_length=255, null=True)
    window_start = models.CharField(max_length=255, null=True)
    rocket_name = models.CharField(max_length=255, blank=True, default="")
    mission_name = models.CharField(max_length=255, blank=True, default="")
    mission_description = models.CharField(max_length=2048, blank=True, default="")
    mission_type = models.CharField(max_length=255, blank=True, default="")
    location_name = models.CharField(max_length=255, blank=True, default="")
    lsp_id = models.IntegerField(blank=True, null=True)
    lsp_name = models.CharField(max_length=255, blank=True, default="")


class VidURLs(models.Model):
    vid_url = models.URLField(max_length=200)
    launch = models.ForeignKey(Launch, related_name='vid_urls', on_delete=models.CASCADE)

    def __unicode__(self):
        return '%s' % self.vid_url


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

