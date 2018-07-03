from bot.app.digest.digest import DigestServer
from celery.schedules import crontab
from celery.task import periodic_task
from celery.utils.log import get_task_logger

from bot.app.repository.launches_repository import LaunchRepository
from bot.app.sync import LaunchLibrarySync

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


@periodic_task(run_every=(crontab(hour='*/1')), options={"expires": 60})
def get_upcoming_launches():
    logger.info('Task - Get Upcoming launches!')
    repository = LaunchRepository()
    repository.get_next_launches(count=100)


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


@periodic_task(run_every=(crontab(minute='*/1')), options={"expires": 60})
def check_next_launch():
    logger.info('Task - Running Notifications...')
    notification = LaunchLibrarySync()
    notification.check_next_launch()


