from bot.app.repository.launches_repository import LaunchRepository
from bot.utils.config import keys
import logging

from spacelaunchnow import config

AUTH_TOKEN_HERE = keys['AUTH_TOKEN_HERE']
APP_ID = keys['APP_ID']
DAEMON_SLEEP = 600
TAG = 'Notification Server'

# Get an instance of a logger
logger = logging.getLogger('bot.notifications')


class LaunchLibrarySync:
    def __init__(self, debug=None, version=None):
        if version is None:
            version = '1.4.1'
        self.repository = LaunchRepository(version=version)
        if debug is None:
            self.DEBUG = config.DEBUG
        else:
            self.DEBUG = debug

    def check_next_launch(self):
        self.repository.get_next_launches(next_count=5, status=1)
        self.repository.get_next_launches(next_count=5, status=2)
        self.repository.get_next_launches(next_count=15)
