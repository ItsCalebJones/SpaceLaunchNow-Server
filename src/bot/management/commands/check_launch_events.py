from django.core.management import BaseCommand
from celery.utils.log import get_task_logger

from bot.app.events.event_tracker import EventTracker
from bot.app.notifications.launch_event_tracker import LaunchEventTracker

logger = get_task_logger('bot')

TAG = 'Notification Server'


class Command(BaseCommand):
    help = 'Run Launch Event Tracker'

    def handle(self, *args, **options):
        logger.info('Running Launch Event Tracker...')
        tracker = LaunchEventTracker()
        tracker.check_events()

        tracker = EventTracker()
        tracker.check_events()
        tracker.check_news_item()

