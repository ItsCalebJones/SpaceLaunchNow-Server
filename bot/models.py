from django.db import models

# http://www.django-rest-framework.org/tutorial/1-serialization/

class Launch(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    status = models.IntegerField()
    netstamp = models.IntegerField()
    wsstamp = models.IntegerField()
    westamp = models.IntegerField()
    isonet = models.DateField()
    isostart = models.DateField()
    isoend = models.DateField()
    inhold = models.BooleanField()
    wasNotifiedTwentyFourHour = models.BooleanField()
    wasNotifiedOneHour = models.BooleanField()
    wasNotifiedTenMinutes = models.BooleanField()
    wasNotifiedDailyDigest = models.BooleanField()
    last_daily_digest_post = models.DateTimeField()
    last_twitter_post = models.DateTimeField()
    location = models.ForeignKey(
        'Location',
        on_delete=models.PROTECT
    )

    def reset_notifier(self):
        self.wasNotifiedTwentyFourHour = False
        self.wasNotifiedOneHour = False
        self.wasNotifiedTenMinutes = False
        self.save()


class Location(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    infoURL = models.URLField()
    wikiURL = models.URLField()
    countryCode = models.CharField(max_length=255)
    pads = models.ForeignKey(
        'Pads',
        on_delete=models.PROTECT
    )


class Pads(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    infoURL = models.URLField()
    wikiURL = models.URLField()
    mapURL = models.URLField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    agencies = models.ForeignKey(
        'Agency',
        on_delete=models.PROTECT
    )


class Agency(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    abbrev = models.CharField(max_length=255)
    countryCode = models.CharField(max_length=255)
    type = models.IntegerField()
    infoURL = models.URLField()
    wikiURL = models.URLField()
    infoURLs = models.ForeignKey(
        'InfoURLs',
        on_delete=models.PROTECT
    )


class Rocket(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    configuration = models.CharField(max_length=255)
    familyName = models.CharField(max_length=255)
    wikiURL = models.URLField()
    infoURLs = models.ForeignKey(
        'InfoURLs',
        on_delete=models.PROTECT
    )
    imageURL = models.URLField()
    imageSizes = models.ForeignKey(
         'ImageSizes',
         on_delete=models.PROTECT
    )
    agencies = models.ForeignKey(
        'Agency',
        on_delete=models.PROTECT
    )


class Mission(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    type = models.IntegerField()
    typeName = models.CharField(max_length=255)


class InfoURLs(models.Model):
    infoURL = models.URLField()


class ImageSizes(models.Model):
    imageSizes = models.IntegerField()
