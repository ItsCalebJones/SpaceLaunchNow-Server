from celery import Celery
from celery.schedules import crontab

from celery.task import periodic_task
from celery.utils.log import get_task_logger

from autoscaler.autoscaler import check_autoscaler

logger = get_task_logger('autoscaler')


@periodic_task(run_every=(crontab(minute='*/5')), options={"expires": 120})
def check_autoscaler_task():
    logger.info('Task - Running autoscaler...')
    check_autoscaler()
