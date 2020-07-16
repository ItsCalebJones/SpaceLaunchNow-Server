import asyncio
import logging

import discord
from discord import Colour
from discord.ext import tasks, commands

from bot.discord.utils import send_to_channel
from bot.models import NewsNotificationChannel, NewsItem

logger = logging.getLogger('bot.discord')


def check_is_removed(channel, args):
    logger.error("Unable to post to this channel: ")
    logger.error(channel)
    logger.error(args)


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


class News(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_news.start()

    def cog_unload(self):
        self.check_news.cancel()

    @commands.command(name='subscribeNews', pass_context=True)
    async def subscribe_news(self, context):
        """Subscribe to Space Launch New's powered by SNAPI.

        Usage: .sln subscribeNews

        """
        channel = context.message.channel
        try:
            owner_id = context.message.guild.owner_id
            author_id = context.message.author.id
        except:
            await channel.send("Only able to run from a text channel.")
            return
        if owner_id == author_id:
            channel, created = NewsNotificationChannel.objects.get_or_create(name=context.message.channel.name,
                                                                             channel_id=context.message.channel.id,
                                                                             server_id=context.message.server.id)
            if channel.subscribed:
                await channel.send("Already subscribed to Space Launch News!")
                return
            channel.subscribed = True
            channel.save()
            await channel.send("Subscribed to Space Launch News!")
        else:
            await channel.send("Only server owners can add Space Launch News notifications.")

    @commands.command(name='removeNews', pass_context=True)
    async def remove_news(self, context):
        """Unsubscribe from Space Launch New's powered by SNAPI.

        Usage: .sln subscribeNews

        """
        channel = context.message.channel
        try:
            owner_id = context.message.guild.owner_id
            author_id = context.message.author.id
        except:
            await channel.send("Only able to run from a server channel.")
            return
        if owner_id == author_id:
            channel, created = NewsNotificationChannel.objects.get_or_create(name=context.message.channel.name,
                                                                             channel_id=context.message.channel.id,
                                                                             server_id=context.message.server.id)
            if not channel.subscribed:
                await channel.send("Not subscribed to Space Launch News!")
                return
            channel.subscribed = False
            channel.save()
            await channel.send("Un-subscribed from Space Launch News!")
        else:
            await channel.send("Only server owners can edit Space Launch News notifications.")

    @tasks.loop(minutes=1)
    async def check_news(self):
        logger.debug("Check News Articles")
        news = NewsItem.objects.filter(read=False)
        logger.info("Found %s articles to read." % len(news))
        for item in news:
            item.read = True
            item.save()
            for channel in NewsNotificationChannel.objects.filter(subscribed=True):
                logger.info("Channel %s" % channel.name)
                logger.info("Channel ID %s" % channel.id)
                try:
                    logger.info("Reading News Articles - %s" % item.title)
                    embed = news_to_embed(item)
                    discord_channel = self.bot.get_channel(id=int(channel.channel_id))
                    await send_to_channel(discord_channel, channel, embed, logger)
                except Exception as e:
                    logger.error("Unable to channel %s-%s - (%s)" % (
                        channel.id,
                        channel.name,
                        channel.server_id))
                    if 'Missing Permissions' in e.args or 'Received NoneType' in e.args:
                        check_is_removed(channel, e.args)
                    continue

    @check_news.before_loop
    async def before_loops(self):
        logger.info("Waiting for startup... (news)")
        await self.bot.wait_until_ready()


def setup(bot):
    news_bot = News(bot)
    bot.add_cog(news_bot)
