# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-09-17 15:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0090_auto_20180917_1533'),
    ]

    operations = [
        migrations.AddField(
            model_name='rocket',
            name='reused',
            field=models.NullBooleanField(),
        ),
    ]
