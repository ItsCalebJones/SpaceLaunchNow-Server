# -*- coding: utf-8 -*-
# Generated by Django 1.11.22 on 2019-07-29 21:04
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0079_auto_20190729_2101'),
    ]

    operations = [
        migrations.AddField(
            model_name='launch',
            name='launch_service_provider',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.Agency'),
        ),
    ]
