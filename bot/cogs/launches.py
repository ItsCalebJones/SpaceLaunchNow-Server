import datetime

import discord
import pytz
from discord import Colour
from discord.ext import commands
from django.db.models import Q
from django.template.defaultfilters import truncatewords

from api.models import Launch


class Launches:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def search(self, context, search: str = None, detailed: str = False):
        """Search for next upcoming space launch.

        Usage: ?search "<search term>" detailed (optional detailed response)

        Examples: ?search "SpaceX" detailed | ?search "ULA"

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
        if detailed == 'detailed':
            embed = launch_to_large_embed(launch)
        else:
            embed = launch_to_small_embed(launch)
        await self.bot.send_message(context.message.channel, embed=embed)

    @commands.command(pass_context=True)
    async def next(self, context, detailed: str = None):
        """Retrieve the next upcoming space launch.

        Usage: ?next detailed (optional detailed response)

        Examples: ?next detailed | ?next

        """
        launch = Launch.objects.filter(net__gte=datetime.datetime.utcnow()).order_by('net').first()
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
    color = get_color(launch.status.id)
    follow_along = "\n\n Follow along on [Android](https://play.google.com/store/apps/details?id=me.calebjones." \
                   "spacelaunchnow&pcampaignid=MKT-Other-global-all-co-prtnr-py-PartBadge-Mar2515-1)," \
                   " [iOS](https://itunes.apple.com/us/app/space-launch-now/id1399715731)" \
                   " or [on the web](https://spacelaunchnow.me/next)"
    lsp_text = "\n\n**Launch Service Provider**\n%s (%s)\n%s\n%s\n%s\n" % (
        launch.rocket.configuration.launch_agency.name, launch.rocket.configuration.launch_agency.abbrev,
        launch.rocket.configuration.launch_agency.administrator, launch.rocket.configuration.launch_agency.info_url,
        launch.rocket.configuration.launch_agency.wiki_url)
    status = "**Status:** %s\n\n" % launch.status.name
    vehicle_text = "\n\n**Launch Vehicle**\n" + launch.rocket.configuration.full_name
    vehicle_text = vehicle_text + "\nLEO: %s (kg) - GTO: %s (kg)" % (launch.rocket.configuration.leo_capacity,
                                                                     launch.rocket.configuration.gto_capacity)
    if len(launch.rocket.firststage.all()) > 0:
        launchers = launch.rocket.firststage.all()
        vehicle_text = vehicle_text + "\n"
        for vehicle in launchers:
            vehicle_text = vehicle_text + "\n"
            if vehicle.type is not None:
                vehicle_text = vehicle_text + "Type: %s \n" % vehicle.type.name
            if vehicle.launcher is not None:
                vehicle_text = vehicle_text + "Serial Number: %s \n" % vehicle.launcher.serial_number
                vehicle_text = vehicle_text + "Flight Proven: %s \n" % vehicle.launcher.flight_proven
                if vehicle.launcher.flight_proven:
                    vehicle_text = vehicle_text + "Flight Number: %s \n" % vehicle.launcher_flight_number
            if vehicle.landing is not None:
                if vehicle.landing.landing_type is not None and vehicle.landing.landing_location is not None:
                    if vehicle.landing.success is None:
                        vehicle_text = vehicle_text + "%s landing at %s" % (vehicle.landing.landing_type.abbrev,
                                                                              vehicle.landing.landing_location.name)
                    elif vehicle.landing.success:
                        vehicle_text = vehicle_text + "%s landed at %s" % (vehicle.landing.landing_type.abbrev,
                                                                             vehicle.landing.landing_location.name)
                    elif not vehicle.landing.success:
                        vehicle_text = vehicle_text + "%s failed to land at %s" % (
                            vehicle.landing.landing_type.abbrev,
                            vehicle.landing.landing_location.name)
        vehicle_text = vehicle_text

    countdown = launch.net - datetime.datetime.now(pytz.utc)
    seconds = countdown.total_seconds()
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    formatted_countdown = ''

    if days != 0:
        formatted_countdown += str(int(days)) + ' Days '
    if hours != 0:
        formatted_countdown += str(int(hours)) + ' Hours '
    if minutes != 0:
        formatted_countdown += str(int(minutes)) + ' Minutes '

    formatted_countdown = '\n**NET In ' + formatted_countdown + '**'

    mission_text = "\n\n**Mission**\n%s\nOrbit: %s\nType: %s" % (launch.mission, launch.mission.orbit,
                                                                 launch.mission.mission_type)
    location = "\n\n**Launch and Landing Location**\n%s\n%s" % (launch.pad.name.split(',', 1)[0],
                                                                launch.pad.location.name)
    description_text = status + launch.mission.description + vehicle_text + mission_text + location + lsp_text + formatted_countdown + follow_along
    embed = discord.Embed(type="rich", title=title,
                          description=description_text,
                          color=color,
                          url=launch.get_full_absolute_url())
    # embed.set_image(url=launch.launcher_config.image_url)
    if launch.rocket.configuration.image_url is not None:
        embed.set_thumbnail(url=launch.rocket.configuration.image_url.url)
    else:
        embed.set_thumbnail(url="https://daszojo4xmsc6.cloudfront.net/static/home/img/launcher.png")
    embed.set_footer(text=launch.net.strftime("NET: %A %B %e, %Y %H:%M %Z"))
    return embed


def launch_to_small_embed(launch, notification="", pre_launch=False):
    title = "%s" % launch.name
    color = get_color(launch.status.id)
    status = "**Status:** %s\n" % launch.status.name
    location = "**Location:** %s\n" % launch.pad.name
    landing = ''
    if len(launch.rocket.firststage.all()) > 0:
        launchers = launch.rocket.firststage.all()
        for vehicle in launchers:
            if vehicle.landing.attempt and vehicle.landing.landing_location:
                landing = "**Landing:** %s (%s)\n" % (vehicle.landing.landing_location.name,
                                                      vehicle.landing.landing_type.abbrev)
                break
    follow_along = "\nFollow along on [Android](https://play.google.com/store/apps/details?id=me.calebjones." \
                   "spacelaunchnow&pcampaignid=MKT-Other-global-all-co-prtnr-py-PartBadge-Mar2515-1)," \
                   " [iOS](https://itunes.apple.com/us/app/space-launch-now/id1399715731)" \
                   " or [on the web](https://spacelaunchnow.me)"
    mission_description = ""
    if launch.mission is not None and launch.mission.description is not None:
        mission_description = "\n%s\n" % (truncatewords(launch.mission.description, 50))
    fail_reason = ""
    if launch.failreason is not None and launch.failreason is not '':
        fail_reason = "\n**Update:** %s\n" % launch.failreason

    formatted_countdown = ''

    if pre_launch:
        countdown = launch.net - datetime.datetime.now(pytz.utc)
        seconds = countdown.total_seconds()
        days, remainder = divmod(seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        if days != 0:
            formatted_countdown += str(int(days)) + ' Days '
        if hours != 0:
            if hours == 23:
                hours = 24
            formatted_countdown += str(int(hours)) + ' Hours '
        if minutes != 0:
            if minutes == 59:
                minutes = 00
            formatted_countdown += str(int(minutes)) + ' Minutes '

        formatted_countdown = '\n**NET In ' + formatted_countdown + '**'

    webcasts = ""
    if launch.vid_urls is not None and len(launch.vid_urls.all()) > 0:
        webcasts = "\n**Video Links:**\n"
        for webcast in launch.vid_urls.all():
            webcasts = webcasts + "[%s](%s)\n" % (webcast, webcast)

    description_text = notification + status + location + landing + fail_reason + mission_description + formatted_countdown + webcasts + follow_along

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
    embed.set_footer(text=launch.net.strftime("NET: %A %B %e, %Y %H:%M %Z"))
    return embed


def event_to_embed(event, notification="", pre_launch=False):
    title = "%s" % event.name
    color = Colour.teal()
    status = "**Type:** %s\n" % event.type.name
    location = "**Location:** %s\n" % event.location
    follow_along = "\nFollow along on [Android](https://play.google.com/store/apps/details?id=me.calebjones." \
                   "spacelaunchnow&pcampaignid=MKT-Other-global-all-co-prtnr-py-PartBadge-Mar2515-1)," \
                   " [iOS](https://itunes.apple.com/us/app/space-launch-now/id1399715731)" \
                   " or [on the web](https://spacelaunchnow.me)"
    event_description = ""
    if event.description is not None:
        event_description = "\n%s\n" % event.description

    formatted_countdown = ''

    if pre_launch:
        countdown = event.date - datetime.datetime.now(pytz.utc)
        seconds = countdown.total_seconds()
        days, remainder = divmod(seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        if days != 0:
            formatted_countdown += str(int(days)) + ' Days '
        if hours != 0:
            if hours == 23:
                hours = 24
            formatted_countdown += str(int(hours)) + ' Hours '
        if minutes != 0:
            if minutes == 59:
                minutes = 00
            formatted_countdown += str(int(minutes)) + ' Minutes '

        formatted_countdown = '\n**Event In ' + formatted_countdown + '**'

    webcasts = ""
    if event.video_url is not None :
        webcasts = "\n**Watch Here:**\n"
        webcasts = webcasts + "[%s](%s)\n" % (event.video_url, event.video_url)

    description_text = notification + status + location + event_description + formatted_countdown + webcasts + follow_along

    embed = discord.Embed(type="rich", title=title,
                          description=description_text,
                          color=color,
                          url=event.get_full_absolute_url())

    if event.feature_image.name is not '':
        try:
            embed.set_thumbnail(url=event.feature_image.url)
        except ValueError:
            embed.set_thumbnail(url="https://daszojo4xmsc6.cloudfront.net/static/home/img/launcher.png")
    else:
        embed.set_thumbnail(url="https://daszojo4xmsc6.cloudfront.net/static/home/img/launcher.png")
    embed.set_footer(text=event.date.strftime("Date: %A %B %e, %Y %H:%M %Z"))
    return embed


def setup(bot):
    bot.add_cog(Launches(bot))
