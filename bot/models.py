from django.db import models
from django.db.models.functions import datetime
from pytz import utc


class Launch(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, blank=True)
    img_url = models.CharField(max_length=255, blank=True, null=True)
    status = models.IntegerField(blank=True, null=True)
    netstamp = models.IntegerField(blank=True, null=True)
    wsstamp = models.IntegerField(blank=True, null=True)
    westamp = models.IntegerField(blank=True, null=True)
    inhold = models.IntegerField(blank=True, null=True)
    net = models.CharField(max_length=255, null=True)
    window_end = models.CharField(max_length=255, null=True)
    window_start = models.CharField(max_length=255, null=True)
    # added = models.DateTimeField(auto_now_add=True)
    # updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = 'Launch'
        verbose_name_plural = 'Launches'


class Location(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, default="")
    country_code = models.CharField(max_length=255, blank=True, default="")
    launch = models.ManyToManyField(Launch, blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = 'Location'
        verbose_name_plural = 'Locations'


class Pad(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, default="")
    info_url = models.URLField(blank=True)
    wiki_url = models.URLField(blank=True)
    map_url = models.URLField(blank=True)
    location = models.ForeignKey(Location, blank=True, on_delete=models.CASCADE)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = 'Pad'
        verbose_name_plural = 'Pads'


class Rocket(models.Model):
    id = models.IntegerField(primary_key=True)
    imageURL = models.URLField()
    name = models.CharField(max_length=255, blank=True, default="")
    configuration = models.CharField(max_length=255, blank=True, default="")
    family_name = models.CharField(max_length=255, blank=True, default="")
    launches = models.ManyToManyField(Launch, blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = 'Rocket'
        verbose_name_plural = 'Rockets'


class Agency(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, default="")
    country_code = models.CharField(max_length=255, blank=True, default="")
    abbrev = models.CharField(max_length=255, blank=True, default="")
    type = models.IntegerField(blank=True, null=True)
    info_url = models.URLField(blank=True)
    wiki_url = models.URLField(blank=True)
    pads = models.ManyToManyField(Pad, blank=True)
    locations = models.ManyToManyField(Location, blank=True)
    rockets = models.ManyToManyField(Rocket, blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = 'Agency'
        verbose_name_plural = 'Agencies'


class LSP(Agency):
    launches = models.ManyToManyField(Launch, blank=True)
    super

    class Meta:
        verbose_name = 'LSP'
        verbose_name_plural = 'LSPs'


class Mission(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, default="")
    description = models.CharField(max_length=2048, blank=True, default="")
    type = models.IntegerField(blank=True, null=True)
    type_name = models.CharField(max_length=255, blank=True, default="")
    launch = models.ForeignKey(Launch, blank=True, on_delete=models.CASCADE)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = 'Mission'
        verbose_name_plural = 'Missions'


class VidURLs(models.Model):
    vid_url = models.URLField(max_length=200)
    launch = models.ForeignKey(Launch, related_name='vid_urls', on_delete=models.CASCADE)

    def __unicode__(self):
        return '%s' % self.vid_url

    class Meta:
        verbose_name = 'Video URL'
        verbose_name_plural = 'Video URLs'


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