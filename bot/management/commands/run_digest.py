from django.core.management import BaseCommand
from bot.app.digest import DigestServer
from celery.utils.log import get_task_logger

logger = get_task_logger('bot')

TAG = 'Digest Server'


class Command(BaseCommand):
    help = 'Run Digest manually.'

    def add_arguments(self, parser):
        feature_parser = parser.add_mutually_exclusive_group(required=False)
        feature_parser.add_argument('--daily', dest='daily', action='store_true')
        feature_parser.add_argument('--weekly', dest='daily', action='store_false')
        parser.add_argument('-version', dest="version", type=str)
        parser.add_argument('-debug', dest="debug", type=bool, const=True, nargs='?')
        parser.set_defaults(daily=True)

    def handle(self, *args, **options):
        logger.info('Running Digest - Daily = %s' % options['daily'])
        debug = options['debug']
        while debug is None:
            response = raw_input('Continue in production mode? (Y/N) ')
            if response == "Y":
                debug = False
            if response == "N":
                debug = True
        version = options['version']
        daily_digest = DigestServer(debug=debug, version=version)
        if options['daily'] is True:
            daily_digest.run(daily=True)
        elif options['daily'] is False:
            daily_digest.run(weekly=True)
