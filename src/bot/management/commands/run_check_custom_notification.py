import logging

from django.core.management import BaseCommand

from bot.app.notifications.launch_event_tracker import LaunchEventTracker

logger = logging.getLogger(__name__)

TAG = "Digest Server"


class Command(BaseCommand):
    help = "Run check custom notifications manually."

    def handle(self, *args, **options):
        logger.info("Check Custom notifications.")
        tracker = LaunchEventTracker()
        tracker.check_custom()
