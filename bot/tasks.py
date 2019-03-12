# coding=utf-8
import os
import stat
import time

from api.management.commands.run_spacex_api_importer import import_core
from api.models import Launch
from datetime import datetime, timedelta

from bot.app.digest.digest import DigestServer
from celery.schedules import crontab
from celery.task import periodic_task
from celery.utils.log import get_task_logger

from bot.app.events.event_tracker import EventTracker
from bot.app.instagram import InstagramBot
from bot.app.notifications.launch_event_tracker import LaunchEventTracker
from bot.app.repository.launches_repository import LaunchRepository
from bot.app.sync import LaunchLibrarySync
from bot.cogs.news import get_news
from bot.cogs.reddit import get_submissions
from bot.cogs.twitter import get_new_tweets
from bot.models import Notification
from bot.utils.util import custom_strftime
from spacelaunchnow import config

logger = get_task_logger('bot.digest')

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

    # Delete notification records from old launches.
    seven_days_past = datetime.today() - timedelta(days=7)
    notifications = Notification.objects.filter(launch__net__lte=seven_days_past)
    notifications.delete()

    # Check for stale launches.
    three_days_past = datetime.today() - timedelta(days=3)
    launches = Launch.objects.filter(last_updated__lte=three_days_past, launch_library=True)
    if len(launches) > 0:
        logger.info("Found stale launches - checking to see if they are deleted from Launch Library")
        repository = LaunchRepository()
        for launch in launches:
            logger.debug("Stale - %s" % launch.name)
            if repository.is_launch_deleted(launch.launch_library_id):
                logger.error("Delete this launch! - %s ID: %d" % (launch.name, launch.launch_library_id))


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
    logger.info('Task - Getting SpaceX cores!')


@periodic_task(run_every=(crontab(minute='*/1')), options={"expires": 60})
def check_next_launch(debug=config.DEBUG):
    logger.info('Task - Running Notifications...')
    notification = LaunchLibrarySync(debug=debug)
    notification.check_next_launch()


@periodic_task(run_every=(crontab(minute='*/1')), options={"expires": 60})
def get_tweets_task():
    logger.info('Task - Running get_new_tweets...')
    get_new_tweets()


@periodic_task(run_every=(crontab(minute='*/5')), options={"expires": 120})
def get_news_task():
    logger.info('Task - Running get_news...')
    get_news()


@periodic_task(run_every=(crontab(minute='*/30')), options={"expires": 120})
def get_reddit_submissions_task():
    logger.info('Task - Running get_reddit_submissions...')
    get_submissions()


@periodic_task(run_every=timedelta(seconds=5), options={"expires": 60})
def launch_tracker():
    logger.info('Task - Running Launch Event Tracker')
    tracker = LaunchEventTracker()
    tracker.check_events()


@periodic_task(run_every=(crontab(minute='*/1')), options={"expires": 60})
def event_tracker():
    logger.info('Task - Running Event Tracker')
    tracker = EventTracker()
    tracker.check_events()


@periodic_task(run_every=(crontab(minute='*/5')), options={"expires": 60})
def get_recent_previous_launches():
    logger.info('Task - Get Recent Previous launches!')
    repository = LaunchRepository()
    repository.get_recent_previous_launches()

    check_for_orphaned_launches()


# @periodic_task(run_every=(crontab(hour='*/6')), options={"expires": 600})
# def set_instagram():
#     logger.info('Task - setting Instagram')
#     try:
#         cache_age = time.time() - os.stat('instagram.cache')[stat.ST_MTIME]
#         if cache_age > 2.592e+6:
#             logger.info('Instagram cache is expired - %d' % cache_age)
#             os.remove('instagram.cache')
#     except FileNotFoundError as error:
#         logger.error(error)
#     instagram = InstagramBot()
#     launch = Launch.objects.filter(net__gte=datetime.now()).order_by('net').first()
#     message = u"""
# 🚀: %s
# 📋: %s
# 📍: %s
# 📅: %s
#     """ % (launch.name, launch.mission.type_name, launch.pad.location.name,
#            custom_strftime("%B {S} at %I:%M %p %Z", launch.net))
#     message = (message[:150]) if len(message) > 150 else message
#     logger.info('Updating Instagram profile to - %s' % message)
#     response = instagram.update_profile(message, launch.get_full_absolute_url())
#     logger.info(response)
