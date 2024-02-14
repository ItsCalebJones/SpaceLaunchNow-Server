import logging

from bot.app.buffer import BufferAPI
from bot.utils.util import get_SLN_url
from spacelaunchnow import settings

logger = logging.getLogger(__name__)


class SocialHandler:
    def __init__(self, debug=settings.DEBUG):
        self.DEBUG = debug
        self.buffer = BufferAPI()

    def send_ten_minute_social(self, event):
        message = "%s in ten minutes!" % event.name
        if event.feature_image and hasattr(event.feature_image, "url"):
            self.buffer.send_to_instagram(message=message, image=event.feature_image.url, now=True)
            logger.info("Sent %s to ALL - with image!", event.name)
        message = message + "\n\n%s" % event.description
        self.buffer.send_to_twitter(message=message, link=get_SLN_url(path="event", object_id=event), now=True)
        self.buffer.send_to_facebook(message=message, link=get_SLN_url(path="event", object_id=event), now=True)
        logger.info("Event %s to Buffer!", event.name)

    def send_webcast_social(self, event):
        if event.video_url:
            message = "%s webcast is live!" % event.name
            if event.feature_image and hasattr(event.feature_image, "url"):
                message += "\n%s" % get_SLN_url(path="event", object_id=event.id)
                self.buffer.send_to_instagram(message=message, image=event.feature_image.url, now=True)
                logger.info("Sent %s to ALL - with image!", event.name)

            self.buffer.send_to_twitter(message=message, link=get_SLN_url(path="event", object_id=event), now=True)
            self.buffer.send_to_facebook(message=message, link=get_SLN_url(path="event", object_id=event), now=True)
            logger.info("Event %s to Buffer!", event.name)
