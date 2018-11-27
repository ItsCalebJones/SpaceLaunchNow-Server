import logging
import re
from datetime import datetime

import pytz
from twitter import Twitter, OAuth, TwitterHTTPError

from bot.utils.config import keys
from bot.utils.util import seconds_to_time
from spacelaunchnow import config

token_key = keys['TOKEN_KEY']
token_secret = keys['TOKEN_SECRET']
consumer_key = keys['CONSUMER_KEY']
consumer_secret = keys['CONSUMER_SECRET']

# Get an instance of a logger
logger = logging.getLogger('notifications')


def get_twitter_message(launch, notification_type):
    current_time = datetime.now(tz=pytz.utc)
    launch_time = launch.net
    diff = int((launch_time - current_time).total_seconds())

    if notification_type == 'netstampChanged':
        return 'SCHEDULE UPDATE: %s now launching from %s in %s. \n %s' % (launch.name, launch.pad.location.name,
                                                                           seconds_to_time(diff),
                                                                           'https://spacelaunchnow.me/launch/%s' %
                                                                           launch.slug)
    elif notification_type == 'success':
        if launch.mission is not None and launch.mission.orbit is not None and launch.mission.orbit.name is not None:
            return '%s was launched successfully from %s to %s by %s. \n %s' % (launch.name, launch.pad.location.name,
                                                                                launch.mission.orbit.name,
                                                                                launch.rocket.configuration.
                                                                                launch_agency.name,
                                                                                'https://spacelaunchnow.me/launch/%s' %
                                                                                launch.slug)
        else:
            return '%s was launched successfully from %s by %s. \n %s' % (launch.name, launch.pad.location.name,
                                                                          launch.rocket.configuration.
                                                                          launch_agency.name,
                                                                          'https://spacelaunchnow.me/launch/%s' %
                                                                          launch.slug)
    elif notification_type == 'failure':
        if launch.mission is not None and launch.mission.orbit is not None and launch.mission.orbit.name is not None:
            return '%s failed to launch from %s to %s by %s. \n %s' % (
                launch.name, launch.pad.location.name,
                launch.mission.orbit.name,
                launch.rocket.configuration.
                    launch_agency.name,
                'https://spacelaunchnow.me/launch/%s' %
                launch.slug)
        else:
            return '%s failed to launch from %s by %s. \n %s' % (launch.name, launch.pad.location.name,
                                                                              launch.rocket.configuration.
                                                                              launch_agency.name,
                                                                              'https://spacelaunchnow.me/launch/%s' %
                                                                              launch.slug)

    elif notification_type == 'partial_failure':
        if launch.mission is not None and launch.mission.orbit is not None and launch.mission.orbit.name is not None:
            return '%s was a partial launch failure from %s to %s by %s. \n %s' % (
                launch.name, launch.pad.location.name,
                launch.mission.orbit.name,
                launch.rocket.configuration.
                    launch_agency.name,
                'https://spacelaunchnow.me/launch/%s' %
                launch.slug)
        else:
            return '%s was a partial launch failure from %s by %s. \n %s' % (launch.name, launch.pad.location.name,
                                                                             launch.rocket.configuration.
                                                                             launch_agency.name,
                                                                             'https://spacelaunchnow.me/launch/%s' %
                                                                             launch.slug)

    elif notification_type == 'inFlight':
        if launch.mission is not None and launch.mission.orbit is not None and launch.mission.orbit.name is not None:
            return '%s currently in flight from %s targeting a %s. \n %s' % (launch.name, launch.pad.location.name,
                                                                             launch.mission.orbit.name,
                                                                             'https://spacelaunchnow.me/launch/%s' %
                                                                             launch.slug)
        else:
            return '%s currently in flight from %s. \n %s' % (launch.name, launch.pad.location.name,
                                                              'https://spacelaunchnow.me/launch/%s' %
                                                              launch.slug)
    elif notification_type == 'oneMinute':
        return '%s launching from %s by %s in less than one minute. \n %s' % (launch.name, launch.pad.location.name,
                                                                              launch.rocket.configuration.launch_agency
                                                                              .name,
                                                                              'https://spacelaunchnow.me/launch/%s' %
                                                                              launch.slug)
    else:
        return '%s launching from %s by %s in %s. \n %s' % (launch.name, launch.pad.location.name,
                                                            launch.rocket.configuration.launch_agency.name,
                                                            seconds_to_time(diff),
                                                            'https://spacelaunchnow.me/launch/%s' % launch.slug)


class TwitterEvents:
    def __init__(self, debug=None):
        if debug is None:
            self.DEBUG = config.DEBUG
        else:
            self.DEBUG = debug

    def send_to_twitter(self, launch, notification, notification_type):
        message = get_twitter_message(launch, notification_type)
        twitter = Twitter(auth=OAuth(token_key, token_secret, consumer_key, consumer_secret))
        twitter_upload = Twitter(domain='upload.twitter.com',
                                 auth=OAuth(token_key, token_secret, consumer_key, consumer_secret))

        try:
            if message.endswith(' (1/1)'):
                message = message[:-6]
            if len(message) > 280:
                end = message[-5:]

                if re.search("([1-9]*/[1-9])", end):
                    message = (message[:271] + '... ' + end)
                else:
                    message = (message[:277] + '...')
            logger.info('Sending to Twitter | %s | %s | DEBUG %s' % (message, str(len(message)), self.DEBUG))
            if not self.DEBUG:
                logger.debug('Sending to twitter - message: %s' % message)
                twitter.statuses.update(status=message)

            notification.last_twitter_post = datetime.now(tz=pytz.utc)
            notification.last_net_stamp = notification.launch.net
            notification.last_net_stamp_timestamp = datetime.now(tz=pytz.utc)
            logger.info('Updating Notification %s to timestamp %s' % (notification.launch.id,
                                                                      notification.last_twitter_post
                                                                      .strftime("%A %d. %B %Y")))

            notification.save()
        except TwitterHTTPError as e:
            logger.error("%s %s" % (str(e), message))
            return None
