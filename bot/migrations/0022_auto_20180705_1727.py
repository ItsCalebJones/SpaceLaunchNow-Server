# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-07-05 17:27
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0021_auto_20180705_1721'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='location',
            name='pad',
        ),
        migrations.RemoveField(
            model_name='pad',
            name='agency_id',
        ),
        migrations.AddField(
            model_name='pad',
            name='location',
            field=models.ForeignKey(blank=True, default=1, on_delete=django.db.models.deletion.CASCADE, related_name='pads', to='bot.Location'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='pad',
            name='info_url',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='pad',
            name='map_url',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='pad',
            name='wiki_url',
            field=models.URLField(blank=True, null=True),
        ),
    ]