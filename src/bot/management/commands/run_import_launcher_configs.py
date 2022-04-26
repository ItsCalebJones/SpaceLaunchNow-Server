import logging

from django.core.management import BaseCommand

from bot.app.repository.launches_repository import LaunchRepository

logger = logging.getLogger(__name__)

TAG = 'Digest Server'


class Command(BaseCommand):
    help = 'Run Get Launcher Configs manually.'

    def handle(self, *args, **options):
        logger.info('Get Launcher Config')
        repository = LaunchRepository()
        repository.get_launcher_configs()
