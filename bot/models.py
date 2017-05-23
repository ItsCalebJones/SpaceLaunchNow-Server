from django.db import models


class Launch(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField()
    status = models.IntegerField()
    isonet = models.DateField()
    isostart = models.DateField()
    isoend = models.DateField()
    inhold = models.BooleanField()
    location = models.ForeignKey(
        'Location',
        on_delete=models.PROTECT
    )


class Location(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField()
    infoURL = models.URLField()
    wikiURL = models.URLField()
    countryCode = models.CharField()
    pads = models.ForeignKey(
        'Pads',
        on_delete=models.PROTECT
    )


class Pads(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField()
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
    name = models.CharField()
    abbrev = models.CharField()
    countryCode = models.CharField()
    type = models.IntegerField()
    infoURL = models.URLField()
    wikiURL = models.URLField()
    infoURLs = models.ForeignKey(
        'InfoURLs',
        on_delete=models.PROTECT
    )


class Rocket(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField()
    configuration = models.CharField()
    familyName = models.CharField()
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
    name = models.CharField()
    description = models.CharField()
    type = models.IntegerField()
    typeName = models.CharField()


class InfoURLs(models.Model):
    infoURL = models.URLField()


class ImageSizes(models.Model):
    imageSizes = models.IntegerField()
