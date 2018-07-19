# coding=utf-8
from api.models import Launch
from datetime import datetime, timedelta

from bot.app.digest.digest import DigestServer
from celery.schedules import crontab
from celery.task import periodic_task
from celery.utils.log import get_task_logger

from bot.app.instagram import InstagramBot
from bot.app.repository.launches_repository import LaunchRepository
from bot.app.sync import LaunchLibrarySync
from bot.models import Notification
from bot.utils.util import custom_strftime

logger = get_task_logger('bot')

TAG = 'Digest Server'


@periodic_task(
    run_every=(crontab(minute=0, hour=12,
                       day_of_week='mon-sun')),
    name="run_daily",
    ignore_result=True,
    options={"expires": 3600}
)
def run_daily():
    logger.info('Task - Running Digest - Daily...')
    daily_digest = DigestServer()
    daily_digest.run(daily=True)


@periodic_task(
    run_every=(crontab(minute=0, hour=12,
                       day_of_week='mon')),
    name="run_weekly",
    ignore_result=True,
    options={"expires": 3600}
)
def run_weekly():
    logger.info('Task - Running Digest - Weekly...')
    daily_digest = DigestServer()
    daily_digest.run(weekly=True)


@periodic_task(run_every=(crontab(hour='*/12')), options={"expires": 60})
def get_upcoming_launches():
    logger.info('Task - Get Upcoming launches!')
    repository = LaunchRepository()
    repository.get_next_launches(next_count=100, all=True)
    check_for_orphaned_launches()


def check_for_orphaned_launches():
    logger.info('Task - Get Upcoming launches!')
    # Query the DB and verify no upcoming launches have failed to update.
    # Most likely requires a new created on and last updated field.
    date = datetime.today() - timedelta(days=7)
    notifications = Notification.objects.filter(launch__net__lte=date)
    notifications.delete()


@periodic_task(
    run_every=(crontab(minute=0, hour=3,
                       day_of_week='mon,wed,fri,sun')),
    name="get_previous",
    ignore_result=True,
    options={"expires": 3600}
)
def get_previous_launches():
    logger.info('Task - Get Previous launches!')
    repository = LaunchRepository()
    repository.get_previous_launches()


@periodic_task(run_every=(crontab(minute='*/1')), options={"expires": 60})
def check_next_launch(debug=False):
    logger.info('Task - Running Notifications...')
    notification = LaunchLibrarySync(debug=debug)
    notification.check_next_launch()

