import logging
import re
from datetime import datetime

import pytz

from bot.app.buffer import BufferAPI, hashtags
from bot.utils.util import get_SLN_url, seconds_to_time
from spacelaunchnow import settings

logger = logging.getLogger(__name__)


def get_message(launch, notification_type):
    current_time = datetime.now(tz=pytz.utc)
    launch_time = launch.net
    diff = int((launch_time - current_time).total_seconds())

    if notification_type == "netstampChanged":
        if launch.status.id == 1:
            content = "LAUNCH SCHEDULE UPDATE\n\n%s now launching from %s in %s." % (
                launch.name,
                launch.pad.location.name,
                seconds_to_time(diff),
            )
            if launch.hashtag:
                content = content + " %s" % launch.hashtag
            return content

        if launch.status.id == 2 or launch.status.id == 5:
            content = "UPDATE: %s launch date has slipped, new date currently unavailable." % launch.name

            if launch.hashtag:
                content = content + " %s" % launch.hashtag
            return content

    elif notification_type == "success":
        if (
            launch.mission is not None
            and launch.mission.orbit is not None
            and launch.mission.orbit.name is not None
            and launch.mission.orbit.name != "Sub-Orbital"
        ):
            content = "%s was launched successfully from %s to %s by %s." % (
                launch.name,
                launch.pad.location.name,
                launch.mission.orbit.name,
                launch.launch_service_provider.name,
            )
            if launch.hashtag:
                content = content + " %s" % launch.hashtag

            return content
        else:
            content = "%s was launched successfully from %s by %s." % (
                launch.name,
                launch.pad.location.name,
                launch.launch_service_provider.name,
            )
            if launch.hashtag:
                content = content + " %s" % launch.hashtag

            return content

    elif notification_type == "failure":
        if (
            launch.mission is not None
            and launch.mission.orbit is not None
            and launch.mission.orbit.name is not None
            and launch.mission.orbit.name != "Sub-Orbital"
        ):
            content = "%s failed to launch from %s to %s by %s." % (
                launch.name,
                launch.pad.location.name,
                launch.mission.orbit.name,
                launch.launch_service_provider.name,
            )

            if launch.hashtag:
                content = content + " %s" % launch.hashtag

            return content
        else:
            content = "%s failed to launch from %s by %s." % (
                launch.name,
                launch.pad.location.name,
                launch.launch_service_provider.name,
            )
            if launch.hashtag:
                content = content + " %s" % launch.hashtag

            return content

    elif notification_type == "partial_failure":
        if (
            launch.mission is not None
            and launch.mission.orbit is not None
            and launch.mission.orbit.name is not None
            and launch.mission.orbit.name != "Sub-Orbital"
        ):
            content = "%s was a partial launch failure from %s to %s by %s." % (
                launch.name,
                launch.pad.location.name,
                launch.mission.orbit.name,
                launch.launch_service_provider.name,
            )

            if launch.hashtag:
                content = content + " %s" % launch.hashtag

            return content
        else:
            content = "%s was a partial launch failure from %s by %s." % (
                launch.name,
                launch.pad.location.name,
                launch.launch_service_provider.name,
            )
            if launch.hashtag:
                content = content + " %s" % launch.hashtag

            return content

    elif notification_type == "inFlight":
        if (
            launch.mission is not None
            and launch.mission.orbit is not None
            and launch.mission.orbit.name is not None
            and launch.mission.orbit.name != "Sub-Orbital"
        ):
            content = "%s currently in flight from %s targeting a %s." % (
                launch.name,
                launch.pad.location.name,
                launch.mission.orbit.name,
            )
            if launch.hashtag:
                content = content + " %s" % launch.hashtag

            return content
        else:
            content = "%s currently in flight from %s." % (launch.name, launch.pad.location.name)

            if launch.hashtag:
                content = content + " %s" % launch.hashtag

            return content

    elif notification_type == "oneMinute":
        if launch.status.id == 1:
            content = "%s launching from %s by %s in less than one minute." % (
                launch.name,
                launch.pad.location.name,
                launch.launch_service_provider.name,
            )

            if launch.hashtag:
                content = content + " %s" % launch.hashtag

            return content

    elif notification_type == "tenMinutes":
        if launch.status.id == 1:
            content = "%s launching from %s by %s in less than ten minutes." % (
                launch.name,
                launch.pad.location.name,
                launch.launch_service_provider.name,
            )
            if launch.hashtag:
                content = content + " %s" % launch.hashtag

            return content

    elif notification_type == "webcastLive":
        content = "%s webcast is now live!" % launch.name

        if launch.hashtag:
            content = content + " %s" % launch.hashtag

        return content

    else:
        if launch.status.id == 1:
            return "%s launching from %s by %s in %s." % (
                launch.name,
                launch.pad.location.name,
                launch.launch_service_provider.name,
                seconds_to_time(diff),
            )
        if launch.status.id == 2 or launch.status.id == 5:
            return "%s might launch from %s by %s in %s." % (
                launch.name,
                launch.pad.location.name,
                launch.launch_service_provider.name,
                seconds_to_time(diff),
            )


class SocialEvents:
    def __init__(self, debug=settings.DEBUG):
        self.DEBUG = debug
        self.buffer = BufferAPI()

    def send_to_all(self, launch, notification_type):
        try:
            self.send_to_twitter(launch, notification_type)
        except Exception as e:
            logger.error(e)

        try:
            self.send_to_instagram(launch, notification_type)
        except Exception as e:
            logger.error(e)

        try:
            self.send_to_facebook(launch, notification_type)
        except Exception as e:
            logger.error(e)

    def send_to_twitter(self, launch, notification_type):
        message = get_message(launch, notification_type)
        if len(message + get_SLN_url(path="launch", object=launch.id)) < 280:
            message = message + "\n%s" % get_SLN_url(path="launch", object=launch)
        if len(message) > 280:
            end = message[-5:]

            if re.search("([1-9]*/[1-9])", end):
                message = message[:271] + "... " + end
            else:
                message = message[:277] + "..."

        logger.info("Twitter Data | %s | %s | DEBUG %s" % (message, str(len(message)), self.DEBUG))

        if not self.DEBUG:
            logger.debug("Sending to twitter via Buffer - message: %s" % message)
            logger.info(self.buffer.send_to_twitter(message=message, now=True))

    def send_to_instagram(self, launch, notification_type):
        message = get_message(launch, notification_type)

        image = None
        if notification_type == "tenMinutes" and launch.infographic_url:
            image = launch.infographic_url.url
            message = message + "\n\nCredit: @geoffdbarrett"
        elif launch.image_url:
            image = launch.image_url.url
        elif launch.rocket.configuration.image_url:
            image = launch.rocket.configuration.image_url.url
        elif launch.infographic_url:
            image = launch.infographic_url.url

        message = message + hashtags

        if not self.DEBUG and image:
            logger.debug("Sending to twitter via Buffer - message: %s" % message)
            logger.info(self.buffer.send_to_instagram(message=message, image=image, now=True))

    def send_to_facebook(self, launch, notification_type):
        message = get_message(launch, notification_type)
        if launch.mission:
            message = message + "\n\n" + launch.mission.description

        if not self.DEBUG:
            logger.debug("Sending to twitter via Buffer - message: %s" % message)
            logger.info(
                self.buffer.send_to_facebook(
                    message=message, link=get_SLN_url(path="launch", object=launch), now=True
                )
            )
