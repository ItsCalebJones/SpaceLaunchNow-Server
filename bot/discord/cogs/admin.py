import logging

from discord import Embed
from discord.ext import tasks, commands

from bot.models import *
from bot.tasks import run_daily

logger = logging.getLogger('bot.discord')


class SLNAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channels.start()

    def cog_unload(self):
        self.channels.cancel()

    @commands.command(name='checkUsage', pass_context=True, hidden=False)
    async def check_usage(self, context):
        """Displays the current Space Launch Bot server count..

        Usage: .sln checkUsage

        Examples: .sln checkUsage
        """
        channel = context.message.channel
        async with channel.typing():
            member_count = 0
            logger.info("IS staff")
            for server in self.bot.guilds:
                if server.id != 264445053596991498:
                    member_count += server.member_count
            message = "Currently serving %s users in %s servers." % (member_count, len(self.bot.guilds))
            logger.info(message)

        await channel.send(content=message)

    @commands.command(name='checkStale', pass_context=True, hidden=True)
    async def stale(self, context):
        """Checks for stale launches.

        Usage: .sln checkStale

        Examples: .sln checkStale
        """
        channel = context.message.channel
        staff_channel = self.bot.get_channel(608829443661889536)
        async with staff_channel.typing():
            if "staff" in [y.name.lower() for y in context.message.author.roles]:
                if channel.id != staff_channel.id:
                    await channel.send("Check for response in <#608829443661889536>")
                data = run_daily(send_webhook=False)
                embeds = []
                for data_embed in data['embeds']:
                    embed = Embed(
                        title=data_embed["title"],
                        description=data_embed["description"]
                    )
                    embeds.append(embed)
                await staff_channel.send(content=data['content'], embed=embeds[0])
            else:
                await channel.send("This is a staff only command.")

    @tasks.loop(hours=1)
    async def channels(self):
        twitter_channels = TwitterNotificationChannel.objects.all()
        reddit_channels = SubredditNotificationChannel.objects.all()
        news_channels = NewsNotificationChannel.objects.all()
        discord_channels = DiscordChannel.objects.all()
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
                        logger.info("Bad perms for channel %s-%s - (%s)" % (channel.id, channel.name, channel.server_id))
                    else:
                        logger.info("Good perms for channel %s-%s - (%s)" % (channel.id, channel.name, channel.server_id))
                except Exception as e:
                    banned_channel.append(channel)
                    logger.error("%s %s-%s - (%s)" % (e, channel.id, channel.name, channel.server_id))
                logger.info("=====================================")
        try:
            for channel in banned_channel:
                if not any(channel.server_id == guild.id for guild in self.bot.guilds):
                    logger.info("Can't find channel %s-%s - (%s)" % (channel.id, channel.name, channel.server_id))
                    channel.delete()

        except Exception as e:
            logger.error(e)


def setup(bot):
    admin_bot = SLNAdmin(bot)
    bot.add_cog(admin_bot)
