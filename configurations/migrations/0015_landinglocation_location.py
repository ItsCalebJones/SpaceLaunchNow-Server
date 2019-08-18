# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-08-09 12:37
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0081_auto_20190730_1810'),
        ('configurations', '0014_dockinglocation_spacestation'),
    ]

    operations = [
        migrations.AddField(
            model_name='landinglocation',
            name='location',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='landing_location', to='api.Location'),
        ),
    ]