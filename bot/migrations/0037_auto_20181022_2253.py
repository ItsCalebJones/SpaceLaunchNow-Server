# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-10-23 02:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0036_auto_20181022_2107'),
    ]

    operations = [
        migrations.AddField(
            model_name='tweet',
            name='default',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='twitternotificationchannel',
            name='default_subscribed',
            field=models.BooleanField(default=False),
        ),
    ]
