# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2019-01-20 18:36
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0058_spacecraftconfiguration_type'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Astronauts',
            new_name='Astronaut',
        ),
        migrations.AlterModelOptions(
            name='astronaut',
            options={'verbose_name': 'Astronaut', 'verbose_name_plural': 'Astronaut'},
        ),
    ]