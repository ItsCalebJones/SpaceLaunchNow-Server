# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from apscheduler.schedulers.background import BackgroundScheduler
from django.apps import AppConfig

from bot.utils.util import log

TAG = "Notification Server"


def start_scheduler():
    log(TAG, "Initializing server...")
    scheduler = BackgroundScheduler()
    scheduler.start()
    log(TAG, "Created background scheduler.")
    scheduler.add_job(run_daily, trigger='cron', day_of_week='mon-sun', hour=10, minute=30)
    scheduler.add_job(run_weekly, trigger='cron', day_of_week='fri', hour=12, minute=30)
    log(TAG, "Added cronjobs to background scheduler.")
    Notifications.NotificationServer(scheduler).run()
    log(TAG, "Notification Server started.")


class BotConfig(AppConfig):
    name = 'bot'

    def ready(self):
        start_scheduler()
