import logging

from discord.ext import commands
from django.db.models import Q

from api.models import Launch
from bot.discord.utils import *

logger = logging.getLogger('bot.discord')


class Launches(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def search(self, context, search: str = None):
        """Search for next upcoming space launch.

        Usage: .sln search "<search term>"

        Examples: .sln search "SpaceX"

        """
        channel = context.message.channel
        try:
            async with channel.typing():
                if search:
                    launch = Launch.objects.filter(Q(launch_service_provider__name__icontains=search) |
                                                   Q(launch_service_provider__abbrev__icontains=search) |
                                                   Q(mission__name__icontains=search) |
                                                   Q(mission__description__icontains=search) |
                                                   Q(rocket__configuration__full_name__icontains=search) |
                                                   Q(name__icontains=search)).filter(
                        net__gte=datetime.datetime.now()).order_by(
                        'net').first()
                    if launch is None:
                        await channel.send("Unable to find a launch for search term \"%s\"." % search)
                        return
                else:
                    await channel.send("Try again like this: ?search \"ULA\"")
                    return
                logger.info("Found launch %s" % launch)
                embed = launch_to_large_embed(launch)
                await channel.send(embed=embed)
        except Exception as e:
            logger.error(e)
            await channel.send("Oops - encountered an error: %s" % e)

    @commands.command(pass_context=True)
    async def next(self, context, detailed: str = None):
        """Retrieve the next upcoming space launch.

        Usage: .sln next

        Examples: .sln next

        """
        channel = context.message.channel
        try:
            launch = Launch.objects.filter(net__gte=datetime.datetime.utcnow()).order_by('net').first()
            if detailed == 'detailed':
                embed = launch_to_large_embed(launch)
            else:
                embed = launch_to_small_embed(launch)
            await channel.send(embed=embed)
        except Exception as e:
            logger.error(e)
            await channel.send("Oops - encountered an error: %s" % e)


def setup(bot):
    bot.add_cog(Launches(bot))
