# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-09-28 16:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0083_auto_20190928_1208'),
        ('bot', '0012_auto_20190826_2004'),
    ]

    operations = [
        migrations.AddField(
            model_name='newsitem',
            name='events',
            field=models.ManyToManyField(blank=True, related_name='events', to='api.Events'),
        ),
        migrations.AddField(
            model_name='newsitem',
            name='launches',
            field=models.ManyToManyField(blank=True, related_name='launches', to='api.Launch'),
        ),
    ]
