from celery.utils.log import get_task_logger
from django.core.management import BaseCommand

from bot.tasks import get_previous_launches

logger = get_task_logger("bot")

TAG = "Digest Server"


class Command(BaseCommand):
    help = "Run Get Previous Launches manually."

    def handle(self, *args, **options):
        logger.info("Get Previous Launches")
        get_previous_launches()
