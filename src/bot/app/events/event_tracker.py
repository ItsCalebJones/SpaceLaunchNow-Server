import datetime
import logging

import pytz
from api.models import Article, Events

from bot.app.events.notification_handler import EventNotificationHandler
from bot.app.notifications.news_notification_handler import NewsNotificationHandler
from bot.models import ArticleNotification
from spacelaunchnow import settings

logger = logging.getLogger(__name__)


class EventTracker:
    def __init__(self, debug=settings.DEBUG):
        self.DEBUG = debug
        self.notification_handler = EventNotificationHandler()
        self.news_notification_handler = NewsNotificationHandler()

    def check_events(self):
        logger.info("Running check_events...")
        time_threshold_10_minute = datetime.datetime.now(tz=pytz.utc) + datetime.timedelta(minutes=10)
        time_threshold_1_hour = datetime.datetime.now(tz=pytz.utc) + datetime.timedelta(hours=1)
        events = Events.objects.filter(date__lte=time_threshold_10_minute, date__gte=datetime.datetime.now(tz=pytz.utc))
        logger.info(f"Found {len(events)} events within 10 minutes.")

        for event in events:
            logger.debug(f"Event: {event.name}")
            logger.debug(f"{event}")
            if event.notifications_enabled:
                if not event.was_notified_ten_minutes:
                    event.was_notified_ten_minutes = True
                    event.save()
                    logger.info(f"Sending {event.name} notification!")
                    self.notification_handler.send_ten_minute_notification(event)

        webcast_events = Events.objects.filter(
            date__lte=time_threshold_1_hour, date__gte=datetime.datetime.now(tz=pytz.utc), webcast_live=True
        )

        for event in webcast_events:

            logger.debug("Web-cast Live! Event: %s", event.name)
            logger.debug(f"{event}")
            if event.notifications_enabled:
                if not event.was_notified_webcast_live:
                    event.was_notified_webcast_live = True
                    event.save()
                    logger.info(f"Sending {event.name} notification!")
                    self.notification_handler.send_webcast_notification(event)

    def check_news_item(self):
        logger.info("Running check news...")
        news_that_need_to_notify = ArticleNotification.objects.filter(
            created_at__gte=datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7),
            should_notify=True,
            was_notified=False,
            sent_at__isnull=True,
        )

        logger.info(f"Found {len(news_that_need_to_notify)} news items.")

        if len(news_that_need_to_notify) > 0:
            for news_item in news_that_need_to_notify:
                logger.info(f"Found {len(news_that_need_to_notify)} news items.")
                item = Article.objects.get(id=news_item.id)
                # Log the news_item with its properties
                logger.info(
                    f"Checking record {news_item.id} was notified: {news_item.was_notified} sent at: {news_item.sent_at} should notify: {news_item.should_notify}"
                )
                if self.check_if_news_notification_allowed:
                    news_item.was_notified = True
                    news_item.sent_at = datetime.datetime.now()
                    news_item.save()
                    logger.info(f"Sending {item.id} {item.title} notification!")
                    self.news_notification_handler.send_notification(item)
                    self.news_notification_handler.send_to_social(item)

    @property
    def check_if_news_notification_allowed(self):
        last_sent = ArticleNotification.objects.filter(sent_at__isnull=False).order_by("-sent_at").first()

        time_since_last_update = 3600
        if last_sent and last_sent.sent_at:
            time_since_last_update = (
                datetime.datetime.now(datetime.timezone.utc) - last_sent.sent_at.replace(tzinfo=datetime.timezone.utc)
            ).total_seconds()

        return time_since_last_update >= 3600
