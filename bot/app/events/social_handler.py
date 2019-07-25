from bot.app.buffer import BufferAPI
import logging
from spacelaunchnow import config


# Get an instance of a logger
logger = logging.getLogger('bot.events')


class SocialHandler:
    def __init__(self, debug=None):
        if debug is None:
            self.DEBUG = config.DEBUG
        else:
            self.DEBUG = debug
        self.buffer = BufferAPI()

    def send_ten_minute_social(self, event):
        message = "%s\n%s" % (event.name, event.description)
        if event.feature_image and hasattr(event.feature_image, 'url'):
            message += "\n %s" % event.get_full_absolute_url
            self.buffer.send_to_all(message=message, image=event.feature_image.url, now=True)
            logger.info('Sent %s to ALL - with image!', event.name)
        else:
            self.buffer.send_to_twitter(message=message, link=event.get_full_absolute_url, now=True)
            self.buffer.send_to_facebook(message=message, link=event.get_full_absolute_url, now=True)
            logger.info('Sent %s to Twitter!', event.name)

    def send_webcast_social(self, event):
        if event.video_url:
            message = "%s\n\n Webcast is now live at %s\n%s" % (event.name, event.video_url, event.description)
            if event.feature_image and hasattr(event.feature_image, 'url'):
                message += "\n %s" % event.get_full_absolute_url
                self.buffer.send_to_all(message=message, image=event.feature_image.url, now=True)
                logger.info('Sent %s to ALL - with image!', event.name)
            else:
                self.buffer.send_to_twitter(message=message, link=event.get_full_absolute_url, now=True)
                self.buffer.send_to_facebook(message=message, link=event.get_full_absolute_url, now=True)
                logger.info('Sent %s to Twitter!', event.name)
