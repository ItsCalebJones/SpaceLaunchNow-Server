# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Agency',
            fields=[
                ('id', models.IntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(default=b'', max_length=255, blank=True)),
                ('abbrev', models.CharField(default=b'', max_length=255, blank=True)),
                ('countryCode', models.CharField(default=b'', max_length=255, blank=True)),
                ('type', models.IntegerField()),
                ('infoURL', models.URLField(blank=True)),
                ('wikiURL', models.URLField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='ImageSizes',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('imageSizes', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='InfoURLs',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('infoURL', models.URLField()),
            ],
        ),
        migrations.CreateModel(
            name='Launch',
            fields=[
                ('id', models.IntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('status', models.IntegerField(blank=True)),
                ('netstamp', models.IntegerField(null=True, blank=True)),
                ('wsstamp', models.IntegerField(null=True, blank=True)),
                ('westamp', models.IntegerField(null=True, blank=True)),
                ('isonet', models.DateField(null=True, blank=True)),
                ('isostart', models.DateField(null=True, blank=True)),
                ('isoend', models.DateField(null=True, blank=True)),
                ('inhold', models.IntegerField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.IntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('infoURL', models.URLField(blank=True)),
                ('wikiURL', models.URLField(blank=True)),
                ('countryCode', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Mission',
            fields=[
                ('id', models.IntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(default=b'', blank=True)),
                ('type', models.IntegerField(null=True, blank=True)),
                ('typeName', models.CharField(max_length=255, null=True, blank=True)),
                ('launch', models.ForeignKey(related_name='missions', to='bot.Launch')),
            ],
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('wasNotifiedTwentyFourHour', models.BooleanField(default=False)),
                ('wasNotifiedOneHour', models.BooleanField(default=False)),
                ('wasNotifiedTenMinutes', models.BooleanField(default=False)),
                ('wasNotifiedDailyDigest', models.BooleanField(default=False)),
                ('last_daily_digest_post', models.DateTimeField(null=True, blank=True)),
                ('last_twitter_post', models.DateTimeField(null=True, blank=True)),
                ('launch', models.OneToOneField(to='bot.Launch')),
            ],
        ),
        migrations.CreateModel(
            name='Pads',
            fields=[
                ('id', models.IntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('infoURL', models.URLField(blank=True)),
                ('wikiURL', models.URLField(blank=True)),
                ('mapURL', models.URLField(blank=True)),
                ('latitude', models.FloatField(blank=True)),
                ('longitude', models.FloatField(blank=True)),
                ('agencies', models.ForeignKey(to='bot.Agency', on_delete=django.db.models.deletion.PROTECT)),
            ],
        ),
        migrations.CreateModel(
            name='Rocket',
            fields=[
                ('id', models.IntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(default=b'', max_length=255, blank=True)),
                ('configuration', models.CharField(default=b'', max_length=255, blank=True)),
                ('familyName', models.CharField(default=b'', max_length=255, blank=True)),
                ('wikiURL', models.URLField(blank=True)),
            ],
        ),
        migrations.AddField(
            model_name='launch',
            name='location',
            field=models.ForeignKey(to='bot.Location', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AddField(
            model_name='launch',
            name='rocket',
            field=models.ForeignKey(to='bot.Rocket', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AddField(
            model_name='agency',
            name='infoURLs',
            field=models.ForeignKey(to='bot.InfoURLs', on_delete=django.db.models.deletion.PROTECT),
        ),
    ]
