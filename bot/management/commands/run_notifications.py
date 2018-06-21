from django.core.management import BaseCommand
from celery.utils.log import get_task_logger

from bot.app.notifications import NotificationServer
from bot.libraries.launchlibrarysdk import LaunchLibrarySDK
from bot.models import Notification
from bot.utils.deserializer import launch_json_to_model

logger = get_task_logger('bot')

TAG = 'Notification Server'


class Command(BaseCommand):
    help = 'Run Notifications manually.'

    def add_arguments(self, parser):
        parser.add_argument('-version', dest="version", type=str)
        parser.add_argument('-debug', '-d', dest="debug", type=bool, const=True, nargs='?')
        parser.add_argument('-test_notification', '-n', dest="test_notification", type=bool, const=False, nargs='?')

    def handle(self, *args, **options):
        logger.info('Running Notifications...')
        debug = options['debug']
        while debug is None:
            response = raw_input('Continue in production mode? (Y/N) ')
            if response == "Y":
                debug = False
            if response == "N":
                debug = True
        version = options['version']
        test_notification = options['test_notification']
        notification = NotificationServer(debug=debug, version=version)
        library = LaunchLibrarySDK(version=version)
        if test_notification:
            response = library.get_next_launch(launch_service_provider="spx")
            if response.status_code is 200:
                response_json = response.json()
                launch_data = response_json['launches']
                for launch in launch_data:
                    launch = launch_json_to_model(launch)
                    notification_obj = Notification.objects.get(launch=launch)
                    # TODO pass in parameter for setting the notification_type
                    notification.send_notification(launch, 'test', notification_obj)
            else:
                logger.error(response.status_code + ' ' + response)

        else:
            notification.check_next_launch()

