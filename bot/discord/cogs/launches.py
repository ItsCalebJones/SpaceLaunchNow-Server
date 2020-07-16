import asyncio
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
    async def next(self, context, search: str = None):
        """Retrieve the next upcoming space launch.

        Usage: .sln next "<search term optional>"

        Examples:
            .sln next
            .sln next "SpaceX"

        """
        channel = context.message.channel
        if search is None:
            search = ""
        try:
            launch = Launch.objects.filter(Q(launch_service_provider__name__icontains=search) |
                                           Q(launch_service_provider__abbrev__icontains=search) |
                                           Q(mission__name__icontains=search) |
                                           Q(mission__description__icontains=search) |
                                           Q(rocket__configuration__full_name__icontains=search) |
                                           Q(name__icontains=search)).filter(
                net__gte=datetime.datetime.now()).order_by(
                'net').first()
            embed = launch_to_small_embed(launch)
            await channel.send(embed=embed)
        except Exception as e:
            logger.error(e)
            await channel.send("Oops - encountered an error: %s" % e)

    @commands.command(pass_context=True)
    async def listUpcoming(self, context, search: str = None):
        """Retrieve the next upcoming space launch.

        Usage: .sln listUpcoming "<search term optional>"

        Examples: .sln listUpcoming SpaceX

        """
        channel = context.message.channel
        if search is None:
            search = ""
        try:
            launches = Launch.objects.filter(Q(launch_service_provider__name__icontains=search) |
                                                   Q(launch_service_provider__abbrev__icontains=search) |
                                                   Q(mission__name__icontains=search) |
                                                   Q(mission__description__icontains=search) |
                                                   Q(rocket__configuration__full_name__icontains=search) |
                                                   Q(name__icontains=search)).filter(
                        net__gte=datetime.datetime.now()).order_by(
                        'net')[:5]

            embed = launch_list_to_embed(launches)
            await channel.send(embed=embed)
        except Exception as e:
            logger.error(e)
            await channel.send("Oops - encountered an error: %s" % e)


def setup(bot):
    bot.add_cog(Launches(bot))
