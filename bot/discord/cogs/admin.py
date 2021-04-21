import asyncio
import logging

import discord
from io import StringIO

from discord import Embed
from discord.ext import tasks, commands
from django.conf import settings
from django.core.management import call_command

from bot.models import *
from bot.tasks import run_daily

logger = logging.getLogger('bot.discord')


class SLNAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channels_loop.start()

    def cog_unload(self):
        self.channels_loop.cancel()

    async def get_channels(self):
        twitter_channels = TwitterNotificationChannel.objects.all()
        reddit_channels = SubredditNotificationChannel.objects.all()
        news_channels = NewsNotificationChannel.objects.all()
        discord_channels = DiscordChannel.objects.all()
        staff_channel = self.bot.get_channel(608829443661889536)
        channel_types = [twitter_channels, reddit_channels, news_channels, discord_channels]
        banned_channel = []
        for channel_type in channel_types:
            for channel in channel_type:
                logger.info("=====================================")
                logger.info("Checking channel %s-%s - (%s)" % (channel.id, channel.name, channel.server_id))
                try:
                    discord_channel = self.bot.get_channel(id=int(channel.channel_id))
                    permission = discord_channel.guild.me.permissions_in(discord_channel)
                    if not permission.send_messages:
                        logger.info(
                            "Bad perms for channel %s-%s - (%s)" % (channel.id, channel.name, channel.server_id))
                    else:
                        logger.info(
                            "Good perms for channel %s-%s - (%s)" % (channel.id, channel.name, channel.server_id))
                except Exception as e:
                    banned_channel.append(channel)
                    logger.info("Removed Channel %s-%s - (%s)" % (channel.id, channel.name, channel.server_id))
                logger.info("=====================================")
        try:
            pending_deletable = []
            for index, channel in enumerate(banned_channel):
                guild_id = int(channel.server_id)
                if not any(guild_id == guild.id for guild in self.bot.guilds):
                    logger.info("Can't find channel %s-%s - (%s)" % (channel.id, channel.name, channel.server_id))
                    pending_deletable.append(channel)
                else:
                    logger.info("Found channel %s-%s - (%s)" % (channel.id, channel.name, channel.server_id))
            if len(pending_deletable) > 0:
                logger.info("Deletable channels %s" % pending_deletable)

                # If Debug == False - delete!
                if not settings.DEBUG and settings.SQUID_BOT_CLIENT_ID == "485112161367097367":
                    # for channel in pending_deletable:
                    #     channel.delete()
                    await staff_channel.send('Deleted stuff.')

        except Exception as e:
            logger.error(e)

    @commands.command(pass_context=True, hidden=True)
    async def checkUsage(self, context):
        """Displays the current Space Launch Bot server count..

        Usage: .sln checkUsage

        Examples: .sln checkUsage
        """
        channel = context.message.channel
        logger.info(f"Processing: {context.message.content}")
        async with channel.typing():
            member_count = 0
            logger.info("IS staff")
            for server in self.bot.guilds:
                if server.id != 264445053596991498:
                    member_count += server.member_count
            message = "Currently serving %s users in %s servers." % (member_count, len(self.bot.guilds))
            logger.info(message)

        await channel.send(content=message)

    # @commands.command(pass_context=True, hidden=True)
    # async def runCommand(self, context, command: str = None):
    #     """Run a Management command.
    #
    #     Usage: .sln runCommand showmigrations
    #
    #     Examples: .sln showmigrations
    #     """
    #     channel = context.message.channel
    #     logger.info(f"Processing: {context.message.content}")
    #     if settings.DEBUG:
    #         staff_channel = self.bot.get_channel(708387934973198438)
    #     else:
    #         staff_channel = self.bot.get_channel(608829443661889536)
    #     if channel.id == staff_channel.id:
    #         content = StringIO()
    #         call_command('api', command, stdout=content)
    #         content.seek(0)
    #         embed = discord.Embed(type="rich", title=f"Ran Command - {command}",
    #                               description=content.read())
    #         await channel.send(embed=embed)
    #     else:
    #         await channel.send("This is a staff only command.")

    @commands.command(name='checkChannels', pass_context=True, hidden=True)
    async def check_channels(self, context):
        channel = context.message.channel
        staff_channel = self.bot.get_channel(608829443661889536)
        async with staff_channel.typing():
            await self.get_channels()

    @tasks.loop(hours=24)
    async def channels_loop(self):
        await self.get_channels()

    @channels_loop.before_loop
    async def before_channels_loop(self):
        await self.bot.wait_until_ready()


def setup(bot):
    admin_bot = SLNAdmin(bot)
    bot.add_cog(admin_bot)
