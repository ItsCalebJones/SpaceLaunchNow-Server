# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Launcher',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('agency', models.CharField(default='Unknown', max_length=50)),
                ('imageURL', models.URLField(blank=True)),
                ('nationURL', models.URLField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='LauncherDetail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('agency', models.CharField(default='Unknown', max_length=50)),
                ('imageURL', models.URLField(blank=True)),
                ('nationURL', models.URLField(blank=True)),
                ('LVInfo', models.CharField(default='Unknown', max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Orbiter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('agency', models.CharField(default='Unknown', max_length=50)),
                ('history', models.CharField(default='', max_length=200)),
                ('details', models.CharField(default='', max_length=200)),
                ('imageURL', models.URLField(blank=True)),
                ('nationURL', models.URLField(blank=True)),
                ('wikiLink', models.URLField(blank=True)),
            ],
        ),
    ]
