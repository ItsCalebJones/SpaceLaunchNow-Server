# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2019-01-31 21:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('configurations', '0012_spacestationtype'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventType',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(blank=True, default='', max_length=255)),
            ],
        ),
    ]
