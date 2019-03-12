from spacelaunchnow import config
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
logger = logging.getLogger('events')


class EventTwitterHandler:
    def __init__(self, debug=None):
        if debug is None:
            self.DEBUG = config.DEBUG
        else:
            self.DEBUG = debug

    def send_ten_minute_tweet(self, event):
        message = "%s in ten minutes!" % event.name
        if event.news_url:
            message += "\n %s" % event.news_url
        twitter = Twitter(auth=OAuth(token_key, token_secret, consumer_key, consumer_secret))
        if event.feature_image and hasattr(event.feature_image, 'url'):
            twitter_upload = Twitter(domain='upload.twitter.com',
                                     auth=OAuth(token_key, token_secret, consumer_key, consumer_secret))
            event.feature_image.open(mode="rb")
            imagedata = event.feature_image.read()
            event.feature_image.close()
            id_img1 = twitter_upload.media.upload(media=imagedata)["media_id_string"]

            # - finally send your tweet with the list of media ids:
            twitter.statuses.update(status=message, media_ids=id_img1)
            logger.info('Sent %s to Twitter - with image!', event.name)
        else:
            twitter.statuses.update(status=message)
            logger.info('Sent %s to Twitter!', event.name)

    def send_webcast_tweet(self, event):
        if event.video_url:
            message = "%s webcast is now live at %s" % (event.name, event.video_url)
            twitter = Twitter(auth=OAuth(token_key, token_secret, consumer_key, consumer_secret))

            twitter.statuses.update(status=message)
            logger.info('Sent %s to Twitter!', event.name)
        else:
            logger.error('No video URL! Not sending a Tweet.', event.name)
