from celery.utils.log import get_task_logger
from django.core.management import BaseCommand

from bot.app.sync.news_sync import get_related_news

logger = get_task_logger("bot.events")

TAG = "Digest Server"


class Command(BaseCommand):
    help = "Run get News manually."

    def handle(self, *args, **options):
        logger.info("Check related news!")
        get_related_news()
        logger.info("Done!")
