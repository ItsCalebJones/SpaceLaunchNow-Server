import asyncio
import logging

from datetime import datetime

import discord
import pytz
import requests
from discord import Colour
from discord.ext import commands
from goose3 import Goose

from bot.models import NewsNotificationChannel, NewsItem

logger = logging.getLogger('bot.discord')


def news_to_embed(news):
    title = "New Article by %s" % news.news_site
    color = Colour.orange()
    description = "[%s](%s)" % (news.title, news.link)
    embed = discord.Embed(type="rich", title=title,
                          description=description,
                          color=color)
    if news.description is not None or news.description is not "":
        embed.add_field(name="Description", value=news.description, inline=True)
    embed.set_image(url=news.featured_image)
    embed.set_footer(text=news.created_at.strftime("%A %B %e, %Y %H:%M %Z • Powered by SNAPI"))
    return embed


def get_news():
    response = requests.get(url='https://api.spaceflightnewsapi.net/articles?limit=5')
    if response.status_code == 200:
        for item in response.json():
            news, created = NewsItem.objects.get_or_create(id=item['_id'])
            if created:
                news.title = item['title']
                news.link = item['url']
                news.featured_image = item['featured_image']
                news.news_site = item['news_site_long']
                news.created_at = datetime.utcfromtimestamp(item['date_published']).replace(tzinfo=pytz.utc)
                news.read = False
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
    return


class News:
    bot = None

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='subscribeNews', pass_context=True)
    async def subscribe_news(self, context):
        """Subscribe to Space Launch New's powered by SNAPI.

        Usage: ?subscribeNews

        """
        try:
            owner_id = context.message.server.owner_id
            author_id = context.message.author.id
        except:
            await self.bot.send_message(context.message.channel, "Only able to run from a server channel.")
            return
        if owner_id == author_id:
            channel, created = NewsNotificationChannel.objects.get_or_create(name=context.message.channel.name,
                                                                             channel_id=context.message.channel.id,
                                                                             server_id=context.message.server.id)
            if channel.subscribed:
                await self.bot.send_message(context.message.channel, "Already subscribed to Space Launch News!")
                return
            channel.subscribed = True
            channel.save()
            await self.bot.send_message(context.message.channel, "Subscribed to Space Launch News!")
        else:
            await self.bot.send_message(context.message.channel,
                                        "Only server owners can add Space Launch News notifications.")

    @commands.command(name='removeNews', pass_context=True)
    async def remove_news(self, context):
        """Unsubscribe from Space Launch New's powered by SNAPI.

        Usage: ?subscribeNews

        """
        try:
            owner_id = context.message.server.owner_id
            author_id = context.message.author.id
        except:
            await self.bot.send_message(context.message.channel, "Only able to run from a server channel.")
            return
        if owner_id == author_id:
            channel, created = NewsNotificationChannel.objects.get_or_create(name=context.message.channel.name,
                                                                             channel_id=context.message.channel.id,
                                                                             server_id=context.message.server.id)
            if not channel.subscribed:
                await self.bot.send_message(context.message.channel, "Not subscribed to Space Launch News!")
                return
            channel.subscribed = False
            channel.save()
            await self.bot.send_message(context.message.channel, "Un-subscribed from Space Launch News!")
        else:
            await self.bot.send_message(context.message.channel,
                                        "Only server owners can edit Space Launch News notifications.")

    async def news_events(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed:
            try:
                await asyncio.wait_for(self.check_news(), 30)
            except Exception as e:
                logger.error(e)
            await asyncio.sleep(5)

    async def check_news(self):
        logger.debug("Check News Articles")
        news = NewsItem.objects.filter(read=False)
        logger.debug("Found %s articles to read." % len(news))
        for item in news:
            item.read = True
            item.save()
            for channel in NewsNotificationChannel.objects.filter(subscribed=True):
                try:
                    logger.info("Reading News Articles - %s" % item.title)
                    embed = news_to_embed(item)
                    await self.bot.send_message(self.bot.get_channel(id=channel.channel_id), embed=embed)
                except Exception as e:
                    logger.error(channel.id)
                    logger.error(channel.name)
                    logger.error(e)


def setup(bot):
    news_bot = News(bot)
    bot.add_cog(news_bot)
    bot.loop.create_task(news_bot.news_events())
