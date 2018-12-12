# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-12-05 02:29
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0014_auto_20181205_0227'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='spacecraftflight',
            options={'verbose_name': 'Spacecraft Flight', 'verbose_name_plural': 'Spacecraft Flights'},
        ),
        migrations.RenameField(
            model_name='spacecraftflight',
            old_name='orbiter',
            new_name='spacecraft',
        ),
        migrations.AlterField(
            model_name='spacecraftflight',
            name='rocket',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='spacecraftflight', to='api.Rocket'),
        ),
    ]