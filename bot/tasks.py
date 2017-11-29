from bot.app.digest import DigestServer
from celery.schedules import crontab
from celery.task import periodic_task
from celery.utils.log import get_task_logger

from bot.app.notifications import NotificationServer

logger = get_task_logger('bot')

TAG = 'Digest Server'


@periodic_task(
    run_every=(crontab(minute=0, hour=12,
                       day_of_week='mon-sun')),
    name="run_daily",
    ignore_result=True
)
def run_daily():
    logger.info('Task - Running Digest - Daily...')
    daily_digest = DigestServer()
    daily_digest.run(daily=True)


@periodic_task(
    run_every=(crontab(minute=0, hour=12,
                       day_of_week='mon')),
    name="run_weekly",
    ignore_result=True
)
def run_weekly():
    logger.info('Task - Running Digest - Weekly...')
    daily_digest = DigestServer()
    daily_digest.run(weekly=True)


@periodic_task(run_every=(crontab(minute='*/1')))
def check_next_launch():
    logger.info('Task - Running Notifications...')
    notification = NotificationServer()
    notification.check_next_launch()
