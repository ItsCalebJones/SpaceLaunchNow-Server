# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-08-21 19:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0056_auto_20180821_1444'),
    ]

    operations = [
        migrations.AlterField(
            model_name='launcher',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
    ]