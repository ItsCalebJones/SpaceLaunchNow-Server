import logging

from datetime import datetime, timedelta

import pytz
import requests
from goose3 import Goose

from api.models import Events, Launch
from bot.models import NewsItem

logger = logging.getLogger('bot.digest')


def get_news(limit=10):
    response = requests.get(url='https://spaceflightnewsapi.net/api/v1/articles?limit=%s' % limit)
    if response.status_code == 200:
        for item in response.json()['docs']:
            news, created = NewsItem.objects.get_or_create(id=item['_id'])
            if created:
                news.title = item['title']
                news.link = item['url']
                news.featured_image = item['featured_image']
                news.news_site = item['news_site_long']
                news.created_at = datetime.utcfromtimestamp(item['date_published']).replace(tzinfo=pytz.utc)
                for event_id in item['events']:
                    try:
                        event = Events.objects.get(id=event_id)
                        news.events.add(event)
                    except Events.DoesNotExist:
                        logger.error("No event found with ID %s" % event_id)
                for launch_id in item['launches']:
                    try:
                        launch = Launch.objects.get(id=launch_id)
                        news.launches.add(launch)
                    except Launch.DoesNotExist:
                        logger.error("No launch found with ID %s" % launch_id)

                if item['featured']:
                    news.should_notify = True
                else:
                    news.should_notify = False
                try:
                    g = Goose()
                    article = g.extract(url=news.link)
                    if article.meta_description is not None and article.meta_description is not "":
                        text = article.meta_description
                    elif article.cleaned_text is not None:
                        text = (article.cleaned_text[:300] + '...') if len(article.cleaned_text) > 300 else article.cleaned_text
                    else:
                        text = None
                    news.description = text
                except Exception as e:
                    logger.error(e)
                logger.info("Added News (%s) - %s - %s" % (news.id, news.title, news.news_site))
                news.save()
            else:
                if news.title != item['title']:
                    news.title = item['title']
                    if (news.created_at - datetime.utcfromtimestamp(item['date_published']).replace(tzinfo=pytz.utc)) > timedelta(1):
                        news.created_at = datetime.utcfromtimestamp(item['date_published']).replace(tzinfo=pytz.utc)
                        news.read = False
                if item['featured']:
                    news.should_notify = True
                else:
                    news.should_notify = False

                found = False
                for event_id in item['events']:
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
                for launch_id in item['launches']:
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
                news.featured_image = item['featured_image']
                news.save()
