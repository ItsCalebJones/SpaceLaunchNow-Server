import logging

from django.core.management import BaseCommand

from bot.app.sync.closure_sync import get_road_closure

logger = logging.getLogger(__name__)

TAG = 'Digest Server'


class Command(BaseCommand):
    help = 'Run get Road Closure manually.'

    def handle(self, *args, **options):
        get_road_closure()
