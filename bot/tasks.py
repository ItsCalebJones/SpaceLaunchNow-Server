from bot.app.DailyDigest import DailyDigestServer
from celery.schedules import crontab
from celery.task import task, periodic_task
from celery.utils.log import get_task_logger

logger = get_task_logger('bot')

TAG = 'Digest Server'


@periodic_task(
    run_every=(crontab(minute=0, hour=10,
                       day_of_week='mon-sun')),
    name="run_daily",
    ignore_result=True
)
def run_daily():
    logger.info('Task - Running Digest - Daily...')
    daily_digest = DailyDigestServer()
    daily_digest.run(daily=True)


@periodic_task(
    run_every=(crontab(minute=0, hour=8,
                       day_of_week='mon')),
    name="run_weekly",
    ignore_result=True
)
def run_weekly():
    logger.info('Task - Running Digest - Weekly...')
    daily_digest = DailyDigestServer()
    daily_digest.run(weekly=True)
