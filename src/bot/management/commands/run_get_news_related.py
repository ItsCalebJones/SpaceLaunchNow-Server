import logging

from django.core.management import BaseCommand

from bot.app.sync.news_sync import get_related_news

logger = logging.getLogger(__name__)

TAG = "Digest Server"


class Command(BaseCommand):
    help = "Run get News manually."

    def handle(self, *args, **options):
        logger.info("Check related news!")
        get_related_news()
        logger.info("Done!")
