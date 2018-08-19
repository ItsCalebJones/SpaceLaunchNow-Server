# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-08-19 04:23
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0052_launch_launch_library'),
    ]

    operations = [
        migrations.AddField(
            model_name='launcher',
            name='audited',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='launcher',
            name='librarian_notes',
            field=models.CharField(blank=True, default='', max_length=2048),
        ),
    ]