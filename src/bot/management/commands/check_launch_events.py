from django.core.management import BaseCommand
from celery.utils.log import get_task_logger

from bot.app.events.event_tracker import EventTracker
from bot.app.notifications.launch_event_tracker import LaunchEventTracker

logger = get_task_logger('bot')

TAG = 'Notification Server'


class Command(BaseCommand):
    help = 'Run Launch Event Tracker'

    def add_arguments(self, parser):
        feature_parser = parser.add_mutually_exclusive_group(required=False)
        feature_parser.add_argument('--launch', dest='launch', action='store_true')
        feature_parser.add_argument('--event', dest='event', action='store_false')

    def handle(self, *args, **options):
        logger.info('Running Tracker...')
        if options['launch']:
            tracker = LaunchEventTracker()
            tracker.check_events()

        if options['event']:
            tracker = EventTracker()
            tracker.check_events()
            tracker.check_news_item()


