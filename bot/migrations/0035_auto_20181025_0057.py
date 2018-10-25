# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-10-25 04:57
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0034_auto_20180927_1846'),
    ]

    operations = [
        migrations.CreateModel(
            name='RedditSubmission',
            fields=[
                ('id', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('user', models.CharField(max_length=255)),
                ('selftext', models.BooleanField(default=False)),
                ('text', models.CharField(max_length=40000)),
                ('link', models.CharField(max_length=255)),
                ('permalink', models.CharField(max_length=255)),
                ('read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Subreddit',
            fields=[
                ('id', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='SubredditNotificationChannel',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('channel_id', models.CharField(max_length=4000, unique=True)),
                ('server_id', models.CharField(max_length=4000)),
                ('name', models.CharField(max_length=4000)),
            ],
            options={
                'verbose_name_plural': 'Reddit Notification Channels',
                'verbose_name': 'Reddit Notification Channel',
            },
        ),
        migrations.CreateModel(
            name='Tweet',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('text', models.CharField(max_length=280)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('read', models.BooleanField(default=False)),
                ('default', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='TwitterNotificationChannel',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('channel_id', models.CharField(max_length=4000, unique=True)),
                ('server_id', models.CharField(max_length=4000)),
                ('name', models.CharField(max_length=4000)),
                ('default_subscribed', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name_plural': 'Twitter Notification Channels',
                'verbose_name': 'Twitter Notification Channel',
            },
        ),
        migrations.CreateModel(
            name='TwitterUser',
            fields=[
                ('user_id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('screen_name', models.CharField(max_length=50)),
                ('name', models.CharField(max_length=50)),
                ('profile_image', models.CharField(max_length=50)),
                ('custom', models.BooleanField(default=False)),
                ('default', models.BooleanField(default=False)),
                ('subscribers', models.ManyToManyField(to='bot.TwitterNotificationChannel')),
            ],
        ),
        migrations.AddField(
            model_name='tweet',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tweets', to='bot.TwitterUser'),
        ),
        migrations.AddField(
            model_name='subreddit',
            name='subscribers',
            field=models.ManyToManyField(to='bot.SubredditNotificationChannel'),
        ),
        migrations.AddField(
            model_name='redditsubmission',
            name='subreddit',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='submissions', to='bot.Subreddit'),
        ),
    ]
