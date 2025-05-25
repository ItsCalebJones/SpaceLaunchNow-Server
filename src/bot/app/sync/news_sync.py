import logging
from datetime import datetime, timedelta, timezone

import requests
from api.models import Article, Events, Launch

from bot.models import ArticleNotification

logger = logging.getLogger(__name__)


def get_news(limit=10):
    response = requests.get(url=f"https://api.spaceflightnewsapi.net/v4/articles/?limit={limit}")
    if response.status_code == 200:
        articles = response.json()
        logger.info(f"Found {len(articles)} articles.")
        for item in articles["results"]:
            save_news_LL(item)


def get_related_news():
    launches = Launch.objects.all()
    for launch in launches:
        url = f"https://api.spaceflightnewsapi.net/v4/articles/?launch={launch.id}"
        logger.debug(f"Looking for related articles - {url}")
        response = requests.get(url=url)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Found {data['count']} articles.")
            for item in data["results"]:
                save_news_LL(item)
    events = Events.objects.all()
    for event in events:
        url = f"https://api.spaceflightnewsapi.net/v4/articles/?event={event.id}"
        logger.debug(f"Looking for related articles - {url}")
        response = requests.get(url=url)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Found {data['count']} articles.")
            for item in data["results"]:
                save_news_LL(item)


def save_news_LL(item):
    news, news_created = Article.objects.get_or_create(id=item["id"])
    record, record_created = ArticleNotification.objects.get_or_create(id=news.id)
    if news_created:
        logger.debug(f"Creating article for article id {item['id']}.")
        news.title = item["title"]
        news.link = item["url"]
        news.featured_image = item["image_url"]
        news.news_site = item["news_site"]
        news.description = item["summary"]
        news.created_at = datetime.strptime(item["published_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        for _event in item["events"]:
            event_id = _event["event_id"]
            try:
                event = Events.objects.get(id=event_id)
                news.events.add(event)
            except Events.DoesNotExist:
                logger.error(f"No event found with ID {event_id}")
        for _launch in item["launches"]:
            launch_id = _launch["launch_id"]
            try:
                launch = Launch.objects.get(id=launch_id)
                news.launches.add(launch)
            except Launch.DoesNotExist:
                logger.error(f"No launch found with ID {launch_id}")
        logger.info(f"Added Article ({news.id}) - {news.title} - {news.news_site}")

        if item["featured"]:
            record.should_notify = True
        else:
            record.should_notify = False

        news.save()
        record.save()

    else:
        logger.info(f"Updating article for article id {item['id']} | {news.id} and record id {record.id}.")
        if news.title != item["title"]:
            news.title = item["title"]
            item_date_str = item["published_at"].replace("Z", "+00:00")
            item_date = datetime.fromisoformat(item_date_str).replace(tzinfo=timezone.utc)
            if news.created_at - item_date > timedelta(1):
                news.created_at = item_date
                logger.info("")
                record.read = True
                record.was_notified = True

        if item["featured"]:
            record.should_notify = True
        else:
            record.should_notify = False

        found = False
        for _event in item["events"]:
            event_id = _event["event_id"]
            for event in news.events.all():
                if event.id == event_id:
                    found = True

            if not found:
                try:
                    event = Events.objects.get(id=event_id)
                    news.events.add(event)
                except Events.DoesNotExist:
                    logger.error(f"No event found with ID {event_id}")

        found = False
        for _launch in item["launches"]:
            launch_id = _launch["launch_id"]
            for launch in news.launches.all():
                if launch.id == launch_id:
                    found = True

            if not found:
                try:
                    launch = Launch.objects.get(id=launch_id)
                    news.launches.add(launch)
                except Launch.DoesNotExist:
                    logger.error(f"No launch found with ID {launch_id}")

        news.news_site = item["news_site"]
        news.description = item["summary"]
        news.link = item["url"]
        news.featured_image = item["image_url"]
        news.save()
        record.save()
        logger.info(f"Article saved for article id {item['id']}.")
