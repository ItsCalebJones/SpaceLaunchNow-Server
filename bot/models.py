from django.db import models


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


class Location(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, default="")
    country_code = models.CharField(max_length=255, blank=True, default="")
    launch = models.ManyToManyField(Launch, blank=True)


class Pad(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, default="")
    info_url = models.URLField(blank=True)
    wiki_url = models.URLField(blank=True)
    map_url = models.URLField(blank=True)
    location = models.ForeignKey(Location, blank=True, on_delete=models.CASCADE)


class Rocket(models.Model):
    id = models.IntegerField(primary_key=True)
    imageURL = models.URLField()
    name = models.CharField(max_length=255, blank=True, default="")
    configuration = models.CharField(max_length=255, blank=True, default="")
    family_name = models.CharField(max_length=255, blank=True, default="")
    launches = models.ManyToManyField(Launch, blank=True)


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


class LSP(Agency):
    launches = models.ManyToManyField(Launch, blank=True)
    super


class Mission(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, default="")
    description = models.CharField(max_length=2048, blank=True, default="")
    type = models.IntegerField(blank=True, null=True)
    type_name = models.CharField(max_length=255, blank=True, default="")
    launch = models.ForeignKey(Launch, blank=True, on_delete=models.CASCADE)


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

