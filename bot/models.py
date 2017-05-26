from django.db import models


class Launch(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    status = models.IntegerField(blank=True)
    netstamp = models.IntegerField(blank=True, null=True)
    wsstamp = models.IntegerField(blank=True, null=True)
    westamp = models.IntegerField(blank=True, null=True)
    inhold = models.IntegerField(blank=True, null=True)
    location = models.ForeignKey(
        'Location',
        on_delete=models.PROTECT
    )
    rocket = models.ForeignKey(
        'Rocket',
        on_delete=models.PROTECT
    )

    def reset_notifier(self):
        self.wasNotifiedTwentyFourHour = False
        self.wasNotifiedOneHour = False
        self.wasNotifiedTenMinutes = False
        self.save()


class Notification(models.Model):
    launch = models.OneToOneField(Launch, on_delete=models.CASCADE)
    wasNotifiedTwentyFourHour = models.BooleanField(blank=True, default=False)
    wasNotifiedOneHour = models.BooleanField(blank=True, default=False)
    wasNotifiedTenMinutes = models.BooleanField(blank=True, default=False)
    wasNotifiedDailyDigest = models.BooleanField(blank=True, default=False)
    last_daily_digest_post = models.DateTimeField(blank=True, null=True)
    last_twitter_post = models.DateTimeField(blank=True, null=True)


class Location(models.Model):
    location_id = models.IntegerField()
    name = models.CharField(max_length=255)
    infoURL = models.URLField(blank=True)
    wikiURL = models.URLField(blank=True)
    countryCode = models.CharField(max_length=255)
    # pads = models.ForeignKey(
    #     'Pads',
    #     on_delete=models.PROTECT
    # )


class Pads(models.Model):
    pad_id = models.IntegerField()
    name = models.CharField(max_length=255)
    infoURL = models.URLField(blank=True)
    wikiURL = models.URLField(blank=True)
    mapURL = models.URLField(blank=True)
    latitude = models.FloatField(blank=True)
    longitude = models.FloatField(blank=True)
    agencies = models.ForeignKey(
        'Agency',
        on_delete=models.PROTECT
    )


class Agency(models.Model):
    agency_id = models.IntegerField()
    name = models.CharField(max_length=255, blank=True, default="")
    abbrev = models.CharField(max_length=255, blank=True, default="")
    countryCode = models.CharField(max_length=255, blank=True, default="")
    type = models.IntegerField()
    infoURL = models.URLField(blank=True)
    wikiURL = models.URLField(blank=True)
    infoURLs = models.ForeignKey(
        'InfoURLs',
        on_delete=models.PROTECT
    )


class Rocket(models.Model):
    rocket_id = models.IntegerField()
    name = models.CharField(max_length=255, blank=True, default="")
    configuration = models.CharField(max_length=255, blank=True, default="")
    familyName = models.CharField(max_length=255, blank=True, default="")
    wikiURL = models.URLField(blank=True)


class Mission(models.Model):
    mission_id = models.IntegerField()
    launch = models.ForeignKey(Launch, related_name='missions', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    type = models.IntegerField(blank=True, null=True)
    typeName = models.CharField(max_length=255, blank=True, null=True)


class InfoURLs(models.Model):
    infoURL = models.URLField()


class ImageSizes(models.Model):
    imageSizes = models.IntegerField()
