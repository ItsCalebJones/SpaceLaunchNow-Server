from api.models import Events
from bot.app.events.notification_handler import EventNotificationHandler
from bot.app.events.twitter_handler import EventTwitterHandler
from spacelaunchnow import config
import datetime
import logging

import pytz

logger = logging.getLogger('events')


class EventTracker:
    def __init__(self, debug=None):
        if debug is None:
            self.DEBUG = config.DEBUG
        else:
            self.DEBUG = debug
        self.twitter = EventTwitterHandler()
        self.notification_handler = EventNotificationHandler()

    def check_events(self):
        time_threshold_10_minute = datetime.datetime.now(tz=pytz.utc) + datetime.timedelta(minutes=10)
        time_threshold_1_hour = datetime.datetime.now(tz=pytz.utc) + datetime.timedelta(hours=1)
        events = Events.objects.filter(date__lte=time_threshold_10_minute,
                                       net__gte=datetime.datetime.now(tz=pytz.utc))

        for event in events:
            if event.notifications_enabled:
                if not event.was_tweeted_ten_minutes:
                    event.was_tweeted_ten_minutes = True
                    event.save()
                    self.twitter.send_ten_minute_tweet(event)
                if not event.was_notified_ten_minutes:
                    event.was_notified_ten_minutes = True
                    event.save()
                    self.notification_handler.send_ten_minute_notification(event)

        webcast_events = Events.objects.filter(date__lte=time_threshold_1_hour,
                                               net__gte=datetime.datetime.now(tz=pytz.utc))

        for event in webcast_events:
            if event.notifications_enabled:
                if not event.was_tweeted_webcast_live:
                    event.was_tweeted_webcast_live = True
                    event.save()
                    self.twitter.send_webcast_tweet(event)
                if not event.was_notified_webcast_live:
                    event.was_notified_webcast_live = True
                    event.save()
                    self.notification_handler.send_webcast_notification(event)
