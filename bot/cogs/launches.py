import datetime

import discord
from discord import Colour
from discord.ext import commands
from django.db.models import Q

from api.models import Launch


class Launches:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def search(self, context, search: str = None, detailed: bool = False):
        """Search for next upcoming space launch.

        Usage: ?search "<search term>" True (optional detailed response)

        Examples: ?search "SpaceX" True | ?search "ULA"

        """
        if search:
            launch = Launch.objects.filter(Q(rocket__configuration__launch_agency__name__icontains=search) |
                                           Q(rocket__configuration__launch_agency__abbrev__icontains=search) |
                                           Q(mission__name__icontains=search) |
                                           Q(mission__description__icontains=search) |
                                           Q(rocket__configuration__full_name__icontains=search) |
                                           Q(name__icontains=search)).filter(net__gte=datetime.datetime.now()).order_by(
                'net').first()
            if launch is None:
                await self.bot.say("Unable to find a launch for search term \"%s\"." % search)
                return
        else:
            await self.bot.say("Try again like this: ?search \"ULA\"")
            return
        if detailed is True:
            embed = launch_to_large_embed(launch)
        else:
            embed = launch_to_small_embed(launch)
        await self.bot.send_message(context.message.channel, embed=embed)

    @commands.command(pass_context=True)
    async def next(self, context, detailed: str = None):
        """Retrieve the next upcoming space launch.

        Usage: ?next True (optional detailed response)

        Examples: ?next True | ?next

        """
        launch = Launch.objects.filter(net__gte=datetime.datetime.now()).order_by('net').first()
        if detailed == 'detailed':
            embed = launch_to_large_embed(launch)
        else:
            embed = launch_to_small_embed(launch)
        await self.bot.send_message(context.message.channel, embed=embed)


def get_color(id):
    if id is 1:
        return Colour.green()
    elif id is 2:
        return Colour.purple()
    elif id is 3:
        return Colour.dark_green()
    elif id is 4:
        return Colour.red()
    elif id is 5:
        return Colour.dark_magenta()
    elif id is 6:
        return Colour.gold()
    elif id is 7:
        return Colour.dark_red()


def launch_to_large_embed(launch):
    title = "%s" % launch.name
    color = get_color(launch.launch_status.id)
    follow_along = "\n\n Follow along on [Android](https://play.google.com/store/apps/details?id=me.calebjones." \
                   "spacelaunchnow&pcampaignid=MKT-Other-global-all-co-prtnr-py-PartBadge-Mar2515-1)," \
                   " [iOS](https://itunes.apple.com/us/app/space-launch-now/id1399715731)" \
                   " or [on the web](https://spacelaunchnow.me/next)"
    lsp_text = "\n\n**Launch Service Provider**\n%s (%s)\n%s\n%s\n%s" % (
        launch.rocket.configuration.launch_agency.name, launch.rocket.configuration.launch_agency.abbrev,
        launch.rocket.configuration.launch_agency.administrator, launch.rocket.configuration.launch_agency.info_url,
        launch.rocket.configuration.launch_agency.wiki_url)
    status = "**Status:** %s\n\n" % launch.launch_status.name
    vehicle_text = "\n\n**Launch Vehicle**\n" + launch.rocket.configuration.full_name
    vehicle_text = vehicle_text + "\nLEO: %s (kg) - GTO: %s (kg)" % (launch.rocket.configuration.leo_capacity,
                                                                     launch.rocket.configuration.gto_capacity)
    if len(launch.launcher.all()) > 0:
        launchers = launch.launcher.all()
        vehicle_text = vehicle_text + "\n"
        for vehicle in launchers:
            vehicle_text = vehicle_text + "-------------------\n"
            vehicle_text = vehicle_text + "Serial Number: %s \n" % vehicle.serial_number
            vehicle_text = vehicle_text + "Flight Proven: %s \n" % vehicle.flight_proven
        vehicle_text = vehicle_text + "-------------------"
    mission_text = "\n\n**Mission**\n%s\nOrbit: %s\nType: %s" % (launch.mission, launch.mission.orbit,
                                                                 launch.mission.mission_type)
    location = "\n\n**Launch and Landing Location**\n%s\n%s" % (launch.pad.name.split(',', 1)[0],
                                                                launch.pad.location.name)
    landing = ""
    if launch.landing_type is not None:
        landing = "\n\n%s landing at %s" % (launch.landing_type.name, launch.landing_location.name)
    description_text = status + launch.mission.description + vehicle_text + mission_text + location + landing + lsp_text + follow_along
    embed = discord.Embed(type="rich", title=title,
                          description=description_text,
                          color=color,
                          url=launch.get_full_absolute_url())
    # embed.set_image(url=launch.launcher_config.image_url)
    if launch.rocket.configuration.image_url is not None:
        embed.set_thumbnail(url=launch.rocket.configuration.image_url.url)
    else:
        embed.set_thumbnail(url="https://daszojo4xmsc6.cloudfront.net/static/home/img/launcher.png")
    embed.set_footer(text=launch.net.strftime("NET: %A %B %e, %Y %m %M %Z "))
    return embed


def launch_to_small_embed(launch, notification=""):
    title = "%s" % launch.name
    color = get_color(launch.launch_status.id)
    status = "**Status:** %s\n\n" % launch.launch_status.name
    follow_along = "\n\n Follow along on [Android](https://play.google.com/store/apps/details?id=me.calebjones." \
                   "spacelaunchnow&pcampaignid=MKT-Other-global-all-co-prtnr-py-PartBadge-Mar2515-1)," \
                   " [iOS](https://itunes.apple.com/us/app/space-launch-now/id1399715731)" \
                   " or [on the web](https://spacelaunchnow.me/next)"
    description_text = notification + status + launch.mission.description + follow_along
    embed = discord.Embed(type="rich", title=title,
                          description=description_text,
                          color=color,
                          url=launch.get_full_absolute_url())

    if launch.rocket.configuration.image_url.name is not '':
        try:
            embed.set_thumbnail(url=launch.rocket.configuration.image_url.url)
        except ValueError:
            embed.set_thumbnail(url="https://daszojo4xmsc6.cloudfront.net/static/home/img/launcher.png")
    else:
        embed.set_thumbnail(url="https://daszojo4xmsc6.cloudfront.net/static/home/img/launcher.png")
    embed.set_footer(text=launch.net.strftime("NET: %A %B %e, %Y %m %M %Z "))
    return embed


def setup(bot):
    bot.add_cog(Launches(bot))
