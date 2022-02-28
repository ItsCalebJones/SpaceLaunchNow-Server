from django.core.management import BaseCommand
from bot.tasks import check_next_launch
from celery.utils.log import get_task_logger

logger = get_task_logger('bot')

TAG = 'Digest Server'


class Command(BaseCommand):
    help = 'Run Check Next Launch manually.'

    def add_arguments(self, parser):
        parser.add_argument('-debug', dest="debug", type=bool, const=True, nargs='?')

    def handle(self, *args, **options):
        logger.info('Check Next Launch')
        debug = options['debug']
        while debug is None:
            response = input('Continue in production mode? (Y/N)')
            if response == "Y":
                debug = False
            if response == "N":
                debug = True
        check_next_launch(debug=debug)
