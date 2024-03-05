import logging

from django.core.management import BaseCommand
from mock_data import load_data

logger = logging.getLogger(__name__)

TAG = "Notification Server"


class Command(BaseCommand):
    help = "Run load data manually."

    def handle(self, *args, **options):
        load_data()
