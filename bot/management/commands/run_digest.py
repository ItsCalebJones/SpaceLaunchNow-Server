from django.core.management import BaseCommand
from bot.app.DailyDigest import DailyDigestServer
from celery.utils.log import get_task_logger

logger = get_task_logger('bot')

TAG = 'Digest Server'


class Command(BaseCommand):
    help = 'Run Digest manually.'

    def add_arguments(self, parser):
        feature_parser = parser.add_mutually_exclusive_group(required=False)
        feature_parser.add_argument('--daily', dest='daily', action='store_true')
        feature_parser.add_argument('--weekly', dest='daily', action='store_false')
        parser.set_defaults(daily=True)

    def handle(self, *args, **options):
        logger.info('Running Digest - Daily = %s' % options['daily'])
        daily_digest = DailyDigestServer()
        if options['daily'] is True:
            daily_digest.run(daily=True)
        elif options['daily'] is False:
            daily_digest.run(weekly=True)
