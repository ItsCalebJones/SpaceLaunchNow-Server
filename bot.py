from discord import Colour
from discord.ext import commands
import discord
import datetime, re
import django
import asyncio
import logging
import traceback
import sys
import os
from collections import Counter

from django.db.models import Q


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "spacelaunchnow.settings")
django.setup()
from bot.models import Notification, DiscordChannel
from api.models import Launch
from spacelaunchnow import config

debug_mode = config.SQUID_BOT_DEBUG_MODE
if not isinstance(debug_mode, bool):
    # SQUID_BOT_DEBUG_MODE can be set to either 'false' or 'no'. Case insensitive
    debug_mode = not (debug_mode.lower() in ['false', 'no'])

github_url = 'https://github.com/bsquidwrd/Squid-Bot'

description = """
Hello! I am a bot written by bsquidwrd with a backbone from Danny.
For the nitty gritty, checkout my GitHub: {0}
""".format(github_url)

initial_extensions = []

discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.CRITICAL)
log = logging.getLogger()
log.setLevel(logging.INFO)
bot_start_time = datetime.datetime.utcnow()

logs_dir = '/webapps/squidbot/logs/{0}/{1}'.format(bot_start_time.strftime('%Y'), bot_start_time.strftime('%m'))
os.makedirs(logs_dir, exist_ok=True)
log_filename = '{0}/squid_bot.{1}.log'.format(logs_dir, bot_start_time.strftime('%Y-%m-%d.%H-%M-%S'))

handler = logging.FileHandler(filename=log_filename, encoding='utf-8', mode='w')
log.addHandler(handler)
help_attrs = dict(hidden=True)
prefix = ['?']
bot = commands.Bot(command_prefix=prefix, description=description, pm_help=None, help_attrs=help_attrs)


@bot.event
async def on_command_error(error, ctx):
    if isinstance(error, commands.NoPrivateMessage):
        await bot.send_message(ctx.message.author, 'This command cannot be used in private messages.')
    elif isinstance(error, commands.DisabledCommand):
        await bot.send_message(ctx.message.author, 'Sorry. This command is disabled and cannot be used.')
    elif isinstance(error, commands.CommandInvokeError):
        print('In {0.command.qualified_name}:'.format(ctx), file=sys.stderr)
        traceback.print_tb(error.original.__traceback__)
        print('{0.__class__.__name__}: {0}'.format(error.original), file=sys.stderr)


@bot.event
async def on_ready():
    print('Logged in as:')
    print('Username: ' + bot.user.name)
    print('ID: ' + bot.user.id)
    print('Debug: ' + str(debug_mode))
    print('------')
    log.info('Logged in as:\nUsername: {0.user.name}\nID: {0.user.id}\nDebug: {1}\n------'.format(bot, str(debug_mode)))
    if not hasattr(bot, 'uptime'):
        bot.uptime = bot_start_time
    squid_bot_game = discord.Game(name='Watching for launches * spacelaunchnow.me', url=github_url, type=0)
    await bot.change_presence(game=squid_bot_game, status=discord.Status.online, afk=False)


@bot.event
async def on_resumed():
    print('resumed...')


@bot.event
async def on_command(command, ctx):
    bot.commands_used[command.name] += 1
    message = ctx.message
    destination = None
    if message.channel.is_private:
        destination = 'Private Message'
    else:
        destination = '#{0.channel.name} ({0.server.name})'.format(message)
    print('{0.timestamp}: {0.author.name} in {1}: {0.content}'.format(message, destination))
    log.info('{0.timestamp}: {0.author.name} in {1}: {0.content}'.format(message, destination))


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)


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
        launch.lsp.name, launch.lsp.abbrev, launch.lsp.administrator, launch.lsp.info_url, launch.lsp.wiki_url)
    status = "**Status:** %s\n\n" % launch.launch_status.name
    vehicle_text = "\n\n**Launch Vehicle**\n" + launch.launcher_config.full_name
    vehicle_text = vehicle_text + "\nLEO: %s (kg) - GTO: %s (kg)" % (launch.launcher_config.leo_capacity,
                                                                     launch.launcher_config.gto_capacity)
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
    if launch.launcher_config.image_url is not None:
        embed.set_thumbnail(url=launch.launcher_config.image_url.url)
    else:
        embed.set_thumbnail(url="https://daszojo4xmsc6.cloudfront.net/static/home/img/launcher.png")
    embed.set_footer(text=launch.net.strftime("NET: %A %B %e, %Y %m %M %Z "))
    return embed


def launch_to_small_embed(launch, notification=None):
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
    if launch.launcher_config.image_url is not None:
        embed.set_thumbnail(url=launch.launcher_config.image_url.url)
    else:
        embed.set_thumbnail(url="https://daszojo4xmsc6.cloudfront.net/static/home/img/launcher.png")
    embed.set_footer(text=launch.net.strftime("NET: %A %B %e, %Y %m %M %Z "))
    return embed


@bot.command(pass_context=True)
async def searchNext(context, search: str = None, detailed: bool = False):
    """Retrieves next launch"""
    if search:
        launch = Launch.objects.filter(Q(lsp__name__icontains=search) |
                                       Q(lsp__abbrev__icontains=search) |
                                       Q(mission__name__icontains=search) |
                                       Q(mission__description__icontains=search) |
                                       Q(launcher_config__full_name__icontains=search) |
                                       Q(name__icontains=search)).filter(net__gte=datetime.datetime.now()).order_by(
            'net').first()
        if launch is None:
            await bot.say("Unable to find a launch for search term \"%s\"." % search)
            return
    else:
        launch = Launch.objects.filter(net__gte=datetime.datetime.now()).order_by('net').first()
    if detailed:
        embed = launch_to_large_embed(launch)
    else:
        embed = launch_to_small_embed(launch)
    await bot.send_message(context.message.channel, embed=embed)


@bot.command(pass_context=True)
async def next(context, detailed: str = None):
    """Retrieves next launch"""
    launch = Launch.objects.filter(net__gte=datetime.datetime.now()).order_by('net').first()
    if detailed == 'detailed':
        embed = launch_to_large_embed(launch)
    else:
        embed = launch_to_small_embed(launch)
    await bot.send_message(context.message.channel, embed=embed)


@bot.command(pass_context=True)
async def addNotificationChannel(context):
    ownerid = context.message.server.owner_id
    authorid = context.message.author.id
    if ownerid == authorid:
        channel = DiscordChannel(name=context.message.channel.name,
                                 channel_id=context.message.channel.id,
                                 server_id=context.message.server.id)
        channel.save()
        await bot.send_message(context.message.channel, "Added this channel to notification list.")
    else:
        await bot.send_message(context.message.channel, "Only server owners can add notification channels.")


@bot.command(pass_context=True)
async def removeNotificationChannel(context):
    ownerid = context.message.server.owner_id
    authorid = context.message.author.id
    if ownerid == authorid:
        channel = DiscordChannel.objects.filter(server_id=context.message.server.id, channel_id=context.message.channel.id).first()
        channel.delete()
        await bot.send_message(context.message.channel, "Removed this channel from the notification list.")
    else:
        await bot.send_message(context.message.channel, "Only server owners can remove notification channels.")


@bot.command(pass_context=True)
async def listNotificationChannels(context):
    ownerid = context.message.server.owner_id
    authorid = context.message.author.id
    if ownerid == authorid:
        channels = DiscordChannel.objects.filter(server_id=context.message.server.id)
        channel_text = "**Here ya go %s!**" % context.message.author.name
        for channel in channels:
            channel_text = channel_text + "\n* %s" % channel.name
        channel_text = channel_text + "\n\nUse ?notificationHelp for help managing notifications."
        await bot.send_message(context.message.channel, channel_text)
    else:
        await bot.send_message(context.message.channel, "Only server owners list notification channels.")


@bot.command(name='git')
async def give_github_url():
    """Gives the URL of the Github repo"""
    await bot.say('You can find out more about me here: {}'.format(github_url))


async def discord_launch_events():
    await bot.wait_until_ready()
    channels = DiscordChannel.objects.all()
    bot_channels = []
    for channel in channels:
        bot_channels.append(bot.get_channel(id=channel.channel_id))
    while not bot.is_closed:
        time_threshold_24_hour = datetime.datetime.now() + datetime.timedelta(hours=24)
        time_threshold_1_hour = datetime.datetime.now() + datetime.timedelta(hours=1)
        time_threshold_10_minute = datetime.datetime.now() + datetime.timedelta(minutes=10)
        time_threshold_1_minute = datetime.datetime.now() + datetime.timedelta(minutes=1)
        time_threshold_past_two_days = datetime.datetime.now() - datetime.timedelta(days=2)

        await check_twenty_four_hour(bot_channels, time_threshold_1_hour, time_threshold_24_hour)

        await check_one_hour(bot_channels, time_threshold_10_minute, time_threshold_1_hour)

        await check_ten_minute(bot_channels, time_threshold_10_minute, time_threshold_1_minute)

        await check_one_minute(bot_channels, time_threshold_1_minute)

        await check_in_flight(bot_channels)

        await check_success(bot_channels, time_threshold_past_two_days, time_threshold_24_hour)

        await asyncio.sleep(5)


async def check_success(bot_channels, time_threshold_past_two_days, time_threshold_24_hour):
    recent_success_launches = Launch.objects.filter(launch_status__id=3,
                                                    net__lte=time_threshold_24_hour,
                                                    net__gte=time_threshold_past_two_days)
    for launch in recent_success_launches:
        notification, created = Notification.objects.get_or_create(launch=launch)
        if not notification.wasNotifiedSuccessDiscord:
            for channel in bot_channels:
                await bot.send_message(channel, embed=launch_to_small_embed(launch, "**Launch was a Success!**\n\n"))
            notification.wasNotifiedSuccessDiscord = True
            notification.save()


async def check_in_flight(bot_channels):
    in_flight_launches = Launch.objects.filter(launch_status__id=6)
    for launch in in_flight_launches:
        notification, created = Notification.objects.get_or_create(launch=launch)
        if not notification.wasNotifiedInFlightDiscord:
            for channel in bot_channels:
                await bot.send_message(channel, embed=launch_to_small_embed(launch, "**Launch is in flight!**\n\n"))
            notification.wasNotifiedInFlightDiscord = True
            notification.save()


async def check_one_minute(bot_channels, time_threshold_1_minute):
    one_minute_launches = Launch.objects.filter(net__lte=time_threshold_1_minute,
                                                net__gte=datetime.datetime.now())
    for launch in one_minute_launches:
        notification, created = Notification.objects.get_or_create(launch=launch)
        if not notification.wasNotifiedOneMinutesDiscord:
            for channel in bot_channels:
                await bot.send_message(channel, embed=launch_to_small_embed(launch, "**Launching in one minute!**\n\n"))
            notification.wasNotifiedOneMinutesDiscord = True
            notification.save()


async def check_ten_minute(bot_channels, time_threshold_10_minute, time_threshold_1_minute):
    ten_minute_launches = Launch.objects.filter(net__lte=time_threshold_10_minute,
                                                net__gte=time_threshold_1_minute)
    for launch in ten_minute_launches:
        notification, created = Notification.objects.get_or_create(launch=launch)
        if not notification.wasNotifiedTenMinutesDiscord:
            for channel in bot_channels:
                await bot.send_message(channel,
                                       embed=launch_to_small_embed(launch, "**Launching in ten minutes!**\n\n"))
            notification.wasNotifiedTenMinutesDiscord = True
            notification.save()


async def check_twenty_four_hour(bot_channels, time_threshold_1_hour, time_threshold_24_hour):
    twenty_four_hour_launches = Launch.objects.filter(net__lte=time_threshold_24_hour,
                                                      net__gte=time_threshold_1_hour)
    for launch in twenty_four_hour_launches:
        notification, created = Notification.objects.get_or_create(launch=launch)
        if not notification.wasNotifiedTwentyFourHourDiscord:
            for channel in bot_channels:
                await bot.send_message(channel,
                                       embed=launch_to_small_embed(launch, "**Launching in twenty four hours!**\n\n"))
            notification.wasNotifiedTwentyFourHourDiscord = True
            notification.save()


async def check_one_hour(bot_channels, time_threshold_10_minute, time_threshold_1_hour):
    one_hour_launches = Launch.objects.filter(net__lte=time_threshold_1_hour,
                                              net__gte=time_threshold_10_minute)
    for launch in one_hour_launches:
        notification, created = Notification.objects.get_or_create(launch=launch)
        if not notification.wasNotifiedOneHourDiscord:
            for channel in bot_channels:
                await bot.send_message(channel, embed=launch_to_small_embed(launch, "**Launching in one hour!**\n\n"))
            notification.wasNotifiedOneHourDiscord = True
            notification.save()


if __name__ == '__main__':
    if any('debug' in arg.lower() for arg in sys.argv):
        bot.command_prefix = '$'

    bot.client_id = config.SQUID_BOT_CLIENT_ID
    bot.commands_used = Counter()
    bot.loop.create_task(discord_launch_events())
    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print('Failed to load extension {}\n{}: {}'.format(extension, type(e).__name__, e))
    bot.run(config.SQUID_BOT_TOKEN)
    handlers = log.handlers[:]
    for hdlr in handlers:
        hdlr.close()
        log.removeHandler(hdlr)
