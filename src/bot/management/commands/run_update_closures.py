from celery.utils.log import get_task_logger
from django.core.management import BaseCommand

from bot.app.sync.closure_sync import get_road_closure

logger = get_task_logger("bot.digest")

TAG = "Digest Server"


class Command(BaseCommand):
    help = "Run get Road Closure manually."

    def handle(self, *args, **options):
        get_road_closure()
