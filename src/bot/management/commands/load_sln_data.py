import logging

from api.tests.mock_data import load_data
from django.core.management import BaseCommand

logger = logging.getLogger(__name__)

TAG = "Notification Server"


class Command(BaseCommand):
    help = "Run load data manually."

    def handle(self, *args, **options):
        load_data()
