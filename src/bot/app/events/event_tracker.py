from api.models import Events, Article
from bot.app.events.notification_handler import EventNotificationHandler
from bot.app.events.social_handler import SocialHandler
from bot.app.notifications.news_notification_handler import NewsNotificationHandler
from bot.models import ArticleNotification
from spacelaunchnow import config
import datetime
import logging

import pytz

logger = logging.getLogger(__name__)


class EventTracker:
    def __init__(self, debug=None):
        if debug is None:
            self.DEBUG = config.DEBUG
        else:
            self.DEBUG = debug
        self.twitter = SocialHandler()
        self.notification_handler = EventNotificationHandler()
        self.news_notification_handler = NewsNotificationHandler()

    def check_events(self):
        logger.info('Running check_events...')
        time_threshold_10_minute = datetime.datetime.now(tz=pytz.utc) + datetime.timedelta(minutes=10)
        time_threshold_1_hour = datetime.datetime.now(tz=pytz.utc) + datetime.timedelta(hours=1)
        events = Events.objects.filter(date__lte=time_threshold_10_minute,
                                       date__gte=datetime.datetime.now(tz=pytz.utc))
        logger.info('Found %s events within 10 minutes.', len(events))

        for event in events:
            logger.debug('Event: %s', event.name)
            logger.debug('%s' % event)
            if event.notifications_enabled:
                if not event.was_tweeted_ten_minutes:
                    event.was_tweeted_ten_minutes = True
                    event.save()
                    logger.info('Sending %s to Twitter!', event.name)
                    self.twitter.send_ten_minute_social(event)
                if not event.was_notified_ten_minutes:
                    event.was_notified_ten_minutes = True
                    event.save()
                    logger.info('Sending %s notification!', event.name)
                    self.notification_handler.send_ten_minute_notification(event)

        webcast_events = Events.objects.filter(date__lte=time_threshold_1_hour,
                                               date__gte=datetime.datetime.now(tz=pytz.utc),
                                               webcast_live=True)

        for event in webcast_events:

            logger.debug('Web-cast Live! Event: %s', event.name)
            logger.debug('%s' % event)
            if event.notifications_enabled:
                if not event.was_tweeted_webcast_live:
                    event.was_tweeted_webcast_live = True
                    event.save()
                    logger.info('Sending %s to Twitter!', event.name)
                    self.twitter.send_webcast_social(event)
                if not event.was_notified_webcast_live:
                    event.was_notified_webcast_live = True
                    event.save()
                    logger.info('Sending %s notification!', event.name)
                    self.notification_handler.send_webcast_notification(event)

    def check_news_item(self):
        logger.debug('Running check news...')
        news_that_need_to_notify = ArticleNotification.objects.filter(
            created_at__gte=datetime.datetime.now() - datetime.timedelta(days=7),
            should_notify=True, was_notified=False)

        logger.debug('Found %d news items.', len(news_that_need_to_notify))

        if len(news_that_need_to_notify) > 0:
            for news_item in news_that_need_to_notify:
                item = Article.objects.get(id=news_item.id)
                if not news_item.was_notified and self.check_if_news_notification_allowed and (
                        datetime.datetime.now().replace(tzinfo=datetime.timezone.utc) - item.created_at.replace(
                    tzinfo=datetime.timezone.utc)) < datetime.timedelta(days=7):
                    news_item.was_notified = True
                    news_item.sent_at = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
                    news_item.save()
                    logger.info('Sending %s notification!', item.title)
                    self.news_notification_handler.send_notification(item)
                    self.news_notification_handler.send_to_social(item)

    @property
    def check_if_news_notification_allowed(self):
        last_sent = ArticleNotification.objects.filter(sent_at__isnull=False).order_by('-sent_at').first()

        time_since_last_update = 3600
        if last_sent and last_sent.sent_at:
            time_since_last_update = (
                    datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc) - last_sent.sent_at.replace(
                tzinfo=datetime.timezone.utc)
            ).total_seconds()

        return time_since_last_update >= 3600
