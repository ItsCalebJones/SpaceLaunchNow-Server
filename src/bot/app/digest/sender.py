import logging
import re

from twitter import Twitter, OAuth, TwitterHTTPError

from spacelaunchnow.config import keys

# import the logging library

# Get an instance of a logger
logger = logging.getLogger('digest')

token_key = keys['TOKEN_KEY']
token_secret = keys['TOKEN_SECRET']
consumer_key = keys['CONSUMER_KEY']
consumer_secret = keys['CONSUMER_SECRET']


def send_twitter_update(message, DEBUG=True, status_id=None):
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
        logger.info('Sending to Twitter | %s | %s | DEBUG %s' % (message, str(len(message)), DEBUG))
        if not DEBUG:
            logger.debug('Sending to twitter - message: %s' % message)
            if status_id:
                response = twitter.statuses.update(status=message, in_reply_to_status_id=status_id)
            else:
                response = twitter.statuses.update(status=message)
            return response['id']

        if DEBUG:
            twitter.direct_messages.new(user="koun7erfit", text=message)
            return None

    except TwitterHTTPError as e:
        logger.error("%s %s" % (str(e), message))
        return None

