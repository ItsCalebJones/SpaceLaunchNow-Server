from bot.app.buffer import BufferAPI
import logging
from spacelaunchnow import config

logger = logging.getLogger(__name__)


class SocialHandler:
    def __init__(self, debug=None):
        if debug is None:
            self.DEBUG = config.DEBUG
        else:
            self.DEBUG = debug
        self.buffer = BufferAPI()

    def send_ten_minute_social(self, event):
        message = "%s in ten minutes!" % event.name
        if event.feature_image and hasattr(event.feature_image, 'url'):
            self.buffer.send_to_instagram(message=message, image=event.feature_image.url, now=True)
            logger.info('Sent %s to ALL - with image!', event.name)
        message = message + "\n\n%s" % event.description
        self.buffer.send_to_twitter(message=message, link=event.get_full_absolute_url(), now=True)
        self.buffer.send_to_facebook(message=message, link=event.get_full_absolute_url(), now=True)
        logger.info('Event %s to Buffer!', event.name)

    def send_webcast_social(self, event):
        if event.video_url:
            message = "%s webcast is live!" % event.name
            if event.feature_image and hasattr(event.feature_image, 'url'):
                message += "\n%s" % event.get_full_absolute_url()
                self.buffer.send_to_instagram(message=message, image=event.feature_image.url, now=True)
                logger.info('Sent %s to ALL - with image!', event.name)

            self.buffer.send_to_twitter(message=message, link=event.get_full_absolute_url(), now=True)
            self.buffer.send_to_facebook(message=message, link=event.get_full_absolute_url(), now=True)
            logger.info('Event %s to Buffer!', event.name)
