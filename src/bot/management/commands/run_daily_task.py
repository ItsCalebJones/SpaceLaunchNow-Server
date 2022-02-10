from celery.utils.log import get_task_logger
from django.core.management import BaseCommand

from bot.tasks import run_daily

logger = get_task_logger("bot")

TAG = "Digest Server"


class Command(BaseCommand):
    help = "Run Check Next Launch manually."

    def handle(self, *args, **options):
        logger.info("Run Daily Check")
        run_daily()
