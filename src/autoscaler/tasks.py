import logging
from celery import Celery
from celery.schedules import crontab
from celery.task import periodic_task
from celery.utils.log import get_task_logger

from autoscaler.autoscaler import check_autoscaler

logger = get_task_logger('autoscaler')

app = Celery()


@periodic_task(run_every=(crontab(minute='*/5')), options={"expires": 120})
def check_autoscaler_task():
    logger.info('Task - Running Autoscaler...')
    check_autoscaler()
    logger.info('Task - Completed Autoscaler...')
