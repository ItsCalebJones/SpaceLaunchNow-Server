# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


# Create your models here.
class Launcher(models.Model):
    name = models.CharField(max_length=50)
    agency = models.CharField(max_length=50, default='Unknown')
    imageURL = models.URLField(blank=True)
    nationURL = models.URLField(blank=True)

    def __str__(self):
        return self.name


class Orbiter(models.Model):
    name = models.CharField(max_length=50)
    agency = models.CharField(max_length=50, default='Unknown')
    history = models.CharField(max_length=200, default='')
    details = models.CharField(max_length=200, default='')
    imageURL = models.URLField(blank=True)
    nationURL = models.URLField(blank=True)
    wikiLink = models.URLField(blank=True)

    def __str__(self):
        return self.name

