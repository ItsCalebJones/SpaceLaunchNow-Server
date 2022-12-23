import logging

from django.core.management import BaseCommand

from bot.app.sync.news_sync import get_news

logger = logging.getLogger(__name__)

TAG = "Digest Server"


class Command(BaseCommand):
    help = "Run get News manually."

    def add_arguments(self, parser):
        parser.add_argument("--limit", dest="limit", type=int)

    def handle(self, *args, **options):
        logger.info("Check Events")
        limit = options["limit"]
        if limit:
            get_news(limit=limit)
        else:
            get_news()
