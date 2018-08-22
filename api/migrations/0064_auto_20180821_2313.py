# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-08-22 03:13
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0063_auto_20180821_1557'),
    ]

    operations = [
        migrations.CreateModel(
            name='AgencyType',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, default='', max_length=255)),
            ],
        ),
        migrations.AddField(
            model_name='agency',
            name='agency_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='agency', to='api.AgencyType'),
        ),
    ]