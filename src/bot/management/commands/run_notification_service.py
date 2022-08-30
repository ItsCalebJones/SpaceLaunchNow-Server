import logging
import os

import time

from django.core.management import BaseCommand

from bot.app.events.event_tracker import EventTracker
from bot.app.notifications.launch_event_tracker import LaunchEventTracker

logger = logging.getLogger(__name__)

TAG = 'Notification Service'


class Command(BaseCommand):
    help = 'Runs the notification service.'

    def handle(self, *args, **options):
        self._run()

    def _run(self):
        self.launch_tracker = LaunchEventTracker()
        self.event_tracker = EventTracker()
        logger.info("Starting health check...")

        while True:
            logger.info("Health check!")
            self.launch_tracker.check_events()
            self.event_tracker.check_events()
            self.event_tracker.check_news_item()
            time.sleep(30)
