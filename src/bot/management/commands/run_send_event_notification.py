import logging
from datetime import datetime, timedelta

from api.models import Events
from django.core.management import BaseCommand

from bot.app.events.notification_handler import EventNotificationHandler

logger = logging.getLogger(__name__)

TAG = "Notification Server"


class Command(BaseCommand):
    help = "Run Notifications manually."

    def add_arguments(self, parser):
        parser.add_argument("-version", dest="version", type=str)

    def handle(self, *args, **options):
        logger.info("Running Notifications...")
        notification = EventNotificationHandler()

        now = datetime.now()
        dayago = now - timedelta(days=1)
        events = Events.objects.all().filter(date__gte=dayago).order_by("date", "id").distinct()
        for event in events[:1]:
            # TODO pass in parameter for setting the notification_type
            notification.send_notification(event, "event_notification")
