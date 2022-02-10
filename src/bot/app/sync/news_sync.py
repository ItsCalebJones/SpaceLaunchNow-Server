import logging

from datetime import datetime, timedelta

import pytz
import requests

from api.models import Events, Launch, Article
from bot.models import ArticleNotification

logger = logging.getLogger('bot.digest')


def get_news(limit=10):
    response = requests.get(url='https://api.spaceflightnewsapi.net/v3/articles?_limit=%s' % limit)
    if response.status_code == 200:
        articles = response.json()
        logger.info("Found %s articles." % len(articles))
        for item in articles:
            save_news_LL(item)


def get_related_news():
    launches = Launch.objects.all()
    for launch in launches:
        url = f'https://api.spaceflightnewsapi.net/v3/articles/launch/{launch.id}'
        logger.debug(f"Looking for related articles - {url}")
        response = requests.get(url=url)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Found {len(data)} articles.")
            for item in data:
                save_news_LL(item)
    events = Events.objects.all()
    for event in events:
        url = f'https://api.spaceflightnewsapi.net/v3/articles/event/{event.id}'
        logger.debug(f"Looking for related articles - {url}")
        response = requests.get(url=url)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Found {len(data)} articles.")
            for item in data:
                save_news_LL(item)


def save_news_LL(item):
    news, news_created = Article.objects.get_or_create(id=item['id'])
    record, record_created = ArticleNotification.objects.get_or_create(id=news.id)
    if news_created:
        logger.debug(f"Creating article for article id {item['id']}.")
        news.title = item['title']
        news.link = item['url']
        news.featured_image = item['imageUrl']
        news.news_site = item['newsSite']
        news.description = item['summary']
        news.created_at = datetime.strptime(item['publishedAt'][:-5], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=pytz.utc)
        for _event in item['events']:
            event_id = _event['id']
            try:
                event = Events.objects.get(id=event_id)
                news.events.add(event)
            except Events.DoesNotExist:
                logger.error("No event found with ID %s" % event_id)
        for _launch in item['launches']:
            launch_id = _launch['id']
            try:
                launch = Launch.objects.get(id=launch_id)
                news.launches.add(launch)
            except Launch.DoesNotExist:
                logger.error("No launch found with ID %s" % launch_id)
        logger.info("Added Article (%s) - %s - %s" % (news.id, news.title, news.news_site))

        if item['featured']:
            record.should_notify = True
        else:
            record.should_notify = False

        news.save()
        record.save()

    else:
        logger.debug(f"Updating article for article id {item['id']}.")
        if news.title != item['title']:
            news.title = item['title']
            if (news.created_at - datetime.strptime(item['publishedAt'][:-5], '%Y-%m-%dT%H:%M:%S').replace(
                    tzinfo=pytz.utc)) > timedelta(1):
                news.created_at = datetime.strptime(item['publishedAt'][:-5], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=pytz.utc)
                record.read = True
                record.was_notified = True

        if item['featured']:
            record.should_notify = True
        else:
            record.should_notify = False

        found = False
        for _event in item['events']:
            event_id = _event['id']
            for event in news.events.all():
                if event.id == event_id:
                    found = True

            if not found:
                try:
                    event = Events.objects.get(id=event_id)
                    news.events.add(event)
                except Events.DoesNotExist:
                    logger.error("No event found with ID %s" % event_id)

        found = False
        for _launch in item['launches']:
            launch_id = _launch['id']
            for launch in news.launches.all():
                if launch.id == launch_id:
                    found = True

            if not found:
                try:
                    launch = Launch.objects.get(id=launch_id)
                    news.launches.add(launch)
                except Launch.DoesNotExist:
                    logger.error("No launch found with ID %s" % launch_id)

        news.link = item['url']
        news.featured_image = item['imageUrl']
        news.save()
        record.save()
        logger.debug(f"Article saved for article id {item['id']}.")
