from django.core.management import BaseCommand
from celery.utils.log import get_task_logger

from bot.app.notifications.notification_handler import NotificationHandler
from bot.libraries.launchlibrarysdk import LaunchLibrarySDK
from bot.models import Notification
from bot.utils.deserializer import launch_json_to_model

logger = get_task_logger('bot')

TAG = 'Notification Server'


class Command(BaseCommand):
    help = 'Run Notifications manually.'

    def add_arguments(self, parser):
        parser.add_argument('-version', dest="version", type=str)

    def handle(self, *args, **options):
        logger.info('Running Notifications...')
        notification = NotificationHandler()
        library = LaunchLibrarySDK()
        response = library.get_next_launches(next_count=1)
        if response.status_code is 200:
            response_json = response.json()
            launch_data = response_json['launches']
            for launch in launch_data:
                launch = launch_json_to_model(launch)
                notification_obj = Notification.objects.get(launch=launch)
                # TODO pass in parameter for setting the notification_type
                notification.send_notification(launch, 'oneHour', notification_obj)
        else:
            logger.error(response.status_code + ' ' + response)


