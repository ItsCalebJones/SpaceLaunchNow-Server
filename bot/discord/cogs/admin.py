import logging

from discord import Embed
from discord.ext import commands
from bot.tasks import run_daily

logger = logging.getLogger('bot.discord')


class SLNAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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


def setup(bot):
    admin_bot = SLNAdmin(bot)
    bot.add_cog(admin_bot)
