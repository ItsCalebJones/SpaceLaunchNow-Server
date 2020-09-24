# coding=utf-8
import json

import requests

from api.models import Launch
from datetime import datetime, timedelta

from celery import Celery

from bot.app.digest.digest import DigestServer
from celery.schedules import crontab
from celery.task import periodic_task
from celery.utils.log import get_task_logger

from bot.app.events.event_tracker import EventTracker

from bot.app.notifications.launch_event_tracker import LaunchEventTracker
from bot.app.repository.launches_repository import LaunchRepository
from bot.app.sync.closure_sync import get_road_closure
from bot.app.sync.launch_library_sync import LaunchLibrarySync
from bot.app.sync.reddit_sync import get_submissions
from bot.app.sync.twitter_sync import get_new_tweets
from bot.app.sync.news_sync import get_news
from bot.models import LaunchNotificationRecord, RedditSubmission, Tweet, ArticleNotification
from spacelaunchnow import config
from celery.schedules import crontab

logger = get_task_logger('bot.digest')

TAG = 'Digest Server'

app = Celery()


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Calls test('hello') every 10 seconds.
    sender.add_periodic_task(10.0, test_task.s('hello'), name='add every 10')

    # Calls test('world') every 30 seconds
    sender.add_periodic_task(30.0, test_task.s('world'), expires=10)


@app.task
def test_task(arg):
    logger.info(arg)


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
                       day_of_week='mon-sun')),
    name="run_daily_cleanup",
    ignore_result=True,
    options={"expires": 3600}
)
def run_daily(send_webhook=True):
    logger.info('Task - Running Digest - Daily Cleanup...')
    data = check_for_orphaned_launches(send_webhook=send_webhook)
    return data


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


@periodic_task(run_every=(crontab(hour='*/2')), options={"expires": 15})
def get_upcoming_launches():
    logger.info('Task - Get Upcoming launches - every two hours!')
    repository = LaunchRepository()
    repository.get_next_launches(next_count=100, all=True)


@periodic_task(run_every=(crontab(hour='*/2')), options={"expires": 15})
def get_road_closures():
    logger.info('Task - Get Road Closures!')
    get_road_closure()


def check_for_orphaned_launches(send_webhook=True):
    logger.info('Task - Get Upcoming launches!')

    # Delete notification records from old launches.
    seven_days_threshhold = datetime.today() - timedelta(days=7)
    thirty_days_threshhold = datetime.today() - timedelta(days=30)

    notifications = LaunchNotificationRecord.objects.filter(launch__net__lte=seven_days_threshhold)
    notifications.delete()

    # TODO only delete if the submission is not stickied.
    # submissions = RedditSubmission.objects.filter(created_at__lte=thirty_days_threshhold)
    # submissions.delete()

    tweet = Tweet.objects.filter(created_at__lte=thirty_days_threshhold)
    tweet.delete()

    news = ArticleNotification.objects.filter(created_at__lte=thirty_days_threshhold)
    news.delete()

    # Check for stale launches.
    three_days_past = datetime.today() - timedelta(days=3)
    launches = Launch.objects.filter(last_updated__lte=three_days_past, launch_library=True)
    count = 0
    stale = []
    if len(launches) > 0:
        logger.info("Found stale launches - checking to see if they are deleted from Launch Library")
        repository = LaunchRepository()
        for launch in launches:
            logger.debug("Stale - %s" % launch.name)
            if repository.is_launch_deleted(launch.launch_library_id):
                stale.append(launch)
                logger.error("Delete this launch! - %s ID: %d" % (launch.name, launch.launch_library_id))

    url = "https://discordapp.com/api/webhooks/681358922774478868/XtzAAHnbE8X930eeXFEwL1bGll-ucFD0xKMDwXUWdHuHvZW8qcqQOYO1eq9Mpyryl2zL"
    data = {}
    data["content"] = "**Daily Stale Checker**"
    data["username"] = "Space Launch Bot"

    # leave this out if you dont want an embed
    data["embeds"] = []
    embed = {}
    description = ""
    title = "Found %s stale launches..." % len(stale)
    for launch in stale:
        description = description + "%s\n [Launch Library](https://launchlibrary.net/1.4/launch/%s) | [Admin](%s)\n\n" % (
            launch.name,
            launch.launch_library_id,
            launch.get_admin_url())
    # for all params, see https://discordapp.com/developers/docs/resources/channel#embed-object
    embed["description"] = (description[:2000] + '\n ... too many stale to show.') if len(description) > 2000 else description
    embed["title"] = title
    data["embeds"].append(embed)
    logger.info(data)

    if send_webhook or len(stale) > 5:
        result = requests.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"})
        try:
            result.raise_for_status()
        except requests.exceptions.HTTPError as err:
            logger.error(err)
        else:
            logger.info("Payload delivered successfully, code {}.".format(result.status_code))
    else:
        logger.info(data)
        return data


@periodic_task(
    run_every=(crontab(minute=0, hour=3,
                       day_of_week='mon-sun')),
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


@periodic_task(run_every=(crontab(minute='*/2')), options={"expires": 60})
def get_tweets_task():
    logger.info('Task - Running get_new_tweets...')
    get_new_tweets()


@periodic_task(run_every=(crontab(minute='*/5')), options={"expires": 120})
def get_news_task():
    logger.info('Task - Running get_news...')
    get_news()


@periodic_task(run_every=(crontab(hour='*/1')), options={"expires": 120})
def get_news_task_hourly():
    logger.info('Task - Running get_news...')
    get_news(limit=50)


@periodic_task(run_every=(crontab(minute='*/30')), options={"expires": 120})
def get_reddit_submissions_task():
    logger.info('Task - Running get_reddit_submissions...')
    get_submissions()


@periodic_task(run_every=timedelta(seconds=15), options={"expires": 5})
def launch_tracker():
    logger.info('Task - Running Launch Event Tracker')
    tracker = LaunchEventTracker()
    tracker.check_events()


@periodic_task(run_every=timedelta(seconds=60), options={"expires": 5})
def event_tracker():
    logger.info('Task - Running Event Tracker')
    tracker = EventTracker()
    tracker.check_events()
    tracker.check_news_item()


@periodic_task(run_every=(crontab(minute='*/5')), options={"expires": 60})
def get_recent_previous_launches():
    logger.info('Task - Get Recent Previous launches!')
    repository = LaunchRepository()
    repository.get_recent_previous_launches()
