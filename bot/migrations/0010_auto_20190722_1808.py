# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2019-07-22 18:08
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0009_newsitem_description'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Notification',
            new_name='LaunchNotificationRecord',
        ),
    ]
