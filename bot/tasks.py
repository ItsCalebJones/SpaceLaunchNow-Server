from bot.app.DailyDigest import DailyDigestServer
from bot.utils.util import log
from celery.schedules import crontab
from celery.task import task, periodic_task
from celery.utils.log import get_task_logger

logger = get_task_logger('bot')

TAG = 'Digest Server'

@periodic_task(
    run_every=(crontab(minute=0, hour=10,
                       day_of_week='mon-sat')),
    name="run_daily",
    ignore_result=True
)
def run_daily():
    logger.info('Running Daily Digest - Daily...')
    daily_digest = DailyDigestServer()
    daily_digest.run(daily=True)


@periodic_task(
    run_every=(crontab(minute=0, hour=10,
                       day_of_week='sun')),
    name="run_weekly",
    ignore_result=True
)
def run_weekly():
    logger.info('Running Daily Digest - Weekly...')
    daily_digest = DailyDigestServer()
    daily_digest.run(weekly=True)

# A periodic task that will run every minute (the symbol "*" means every)
@periodic_task(run_every=(crontab(hour="*", minute="*", day_of_week="*")))
def run_daily():
    logger.info('Running Daily Digest - Daily...')
    daily_digest = DailyDigestServer()
    daily_digest.run(daily=True)
