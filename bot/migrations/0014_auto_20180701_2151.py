# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-07-02 01:51
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0013_notification_last_notification_recipient_count'),
    ]

    operations = [
        migrations.CreateModel(
            name='InfoURLs',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('info_url', models.URLField()),
            ],
            options={
                'verbose_name': 'Info URL',
                'verbose_name_plural': 'Info URLs',
            },
        ),
        migrations.RemoveField(
            model_name='location',
            name='launch',
        ),
        migrations.RemoveField(
            model_name='lsp',
            name='launches',
        ),
        migrations.RemoveField(
            model_name='mission',
            name='launch',
        ),
        migrations.RemoveField(
            model_name='rocket',
            name='launches',
        ),
        migrations.AddField(
            model_name='launch',
            name='failreason',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='launch',
            name='hashtag',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='launch',
            name='holdreason',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='launch',
            name='isoend',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='launch',
            name='isonet',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='launch',
            name='isostart',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='launch',
            name='location',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='location', to='bot.Location'),
        ),
        migrations.AddField(
            model_name='launch',
            name='lsp',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='lsp', to='bot.LSP'),
        ),
        migrations.AddField(
            model_name='launch',
            name='mission',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='mission', to='bot.Mission'),
        ),
        migrations.AddField(
            model_name='launch',
            name='probability',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='launch',
            name='rocket',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='rocket', to='bot.Rocket'),
        ),
        migrations.AddField(
            model_name='launch',
            name='tbddate',
            field=models.NullBooleanField(default=False),
        ),
        migrations.AddField(
            model_name='launch',
            name='tbdtime',
            field=models.NullBooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='launch',
            name='inhold',
            field=models.NullBooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='launch',
            name='net',
            field=models.DateTimeField(max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='launch',
            name='window_end',
            field=models.DateTimeField(max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='launch',
            name='window_start',
            field=models.DateTimeField(max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='pad',
            name='location',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='pads', to='bot.Location'),
        ),
        migrations.AddField(
            model_name='infourls',
            name='launch',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='info_urls', to='bot.Launch'),
        ),
    ]
