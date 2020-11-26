import asyncio
import logging

from discord.ext import tasks, commands
from django.db.models import Q
from django.template import defaultfilters

from api.models import Launch, Events
from bot.discord.utils import *
from bot.models import DiscordChannel, LaunchNotificationRecord

logger = logging.getLogger('bot.discord.notifier')
message_number = 0


def check_is_removed(channel, args):
    logger.error("Unable to post to this channel: ")
    logger.error(channel)
    logger.error(args)


class Notifications(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.discord_launch_events.start()
        self.set_bot_description.start()
        global message_number
        message_number = 0

    def cog_unload(self):
        self.discord_launch_events.cancel()
        self.set_bot_description.cancel()

    @commands.command(name='addNotificationChannel', pass_context=True)
    async def addNotificationChannel(self, context):
        """Subscribe current channel to launch notifications.

        Note: Only server owners can perform this action.

        Usage: .sln addNotificationChannel
        """
        channel = context.message.channel

        try:
            ownerid = context.message.guild.owner_id
            authorid = context.message.author.id

        except:
            await channel.send("Only able to run from a server channel.")
            return
        if ownerid == authorid:
            logger.info("Attempting to add %s (%s) from %s (%s) to notification list." % (context.message.channel,
                                                                                          context.message.channel.id,
                                                                                          context.message.guild,
                                                                                          context.message.guild.id))
            try:
                discord_channel = DiscordChannel(name=context.message.channel.name,
                                                 channel_id=str(context.message.channel.id),
                                                 server_id=str(context.message.guild.id))
                discord_channel.save()
            except Exception as e:
                logger.error("Unable to add %s to notification list. %s" % (channel.name, e))
                await channel.send("Unable to add %s to notification list. %s" % (channel.name, e))
            await channel.send("Added %s to notification list." % channel.name)
        else:
            await channel.send("Only server owners can add notification channels.")

    @commands.command(name='removeNotificationChannel',pass_context=True)
    async def removeNotificationChannel(self, context):
        """Remove current channel from launch notifications.

        Note: Only server owners can perform this action.

        Usage: .sln removeNotificationChannel
        """
        channel = context.message.channel
        try:
            ownerid = context.message.guild.owner_id
            authorid = context.message.author.id
        except:
            await channel.send("Only able to run from a server channel.")
            return
        if ownerid == authorid:
            discord_channel = DiscordChannel.objects.filter(server_id=str(context.message.guild.id),
                                                            channel_id=context.message.channel.id).first()
            discord_channel.delete()
            await channel.send("Removed %s from notification list." % channel.name)
        else:
            await channel.send("Only server owners can remove notification channels.")

    @commands.command(name='listNotificationChannels', pass_context=True)
    async def listNotificationChannels(self, context):
        """List all channels that are subscribed to launch notifications.

        Note: Only server owners can perform this action.

        Usage: .sln listNotificationChannels
        """
        channel = context.message.channel
        try:
            ownerid = context.message.guild.owner_id
            authorid = context.message.author.id
        except:
            await channel.send("Only able to run from a server channel.")
            return
        if ownerid == authorid:
            logger.info(context.message.guild.id)
            discord_channels = DiscordChannel.objects.filter(server_id=str(context.message.guild.id))
            logger.info(discord_channels)
            channel_text = "**Here ya go %s!**" % context.message.author.name
            if len(discord_channels) > 0:
                for discord_channel in discord_channels:
                    channel_text = channel_text + "\n* %s" % discord_channel.name
            else:
                channel_text = channel_text + "\n\nNo channels on this guild subscribed to any notifications."
            channel_text = channel_text + "\n\nUse '.sln notifications' for help managing notifications."
            await channel.send(channel_text)
        else:
            await channel.send("Only server owners list notification channels.")

    async def check_success(self, bot_channels, time_threshold_past_two_days, time_threshold_24_hour):
        logger.debug("Checking successful launches...")
        recent_success_launches = Launch.objects.filter(Q(status__id=3) | Q(status__id=4) | Q(status__id=7),
                                                        net__lte=time_threshold_24_hour,
                                                        net__gte=time_threshold_past_two_days)
        for launch in recent_success_launches:
            logger.debug("Found %s successful launches" % len(recent_success_launches))
            notification, created = LaunchNotificationRecord.objects.get_or_create(launch_id=launch.id)
            if not notification.wasNotifiedSuccessDiscord:
                notification.wasNotifiedSuccessDiscord = True
                notification.save()
                logger.info("Success - Launch Notification for %s" % launch.name)
                embed = launch_to_small_embed(launch, "**Launch was a %s!**\n\n" % launch.status.abbrev,
                                              pre_launch=False)
                await self.send_embeds(embed, bot_channels)

    async def check_in_flight(self, bot_channels):
        logger.debug("Checking in-flight launches...")
        in_flight_launches = Launch.objects.filter(status__id=6)
        for launch in in_flight_launches:
            logger.debug("Found %s in flight launches" % len(in_flight_launches))
            notification, created = LaunchNotificationRecord.objects.get_or_create(launch_id=launch.id)
            if not notification.wasNotifiedInFlightDiscord:
                notification.wasNotifiedInFlightDiscord = True
                notification.save()
                logger.info("In-Flight - Launch Notification for %s" % launch.name)
                embed = launch_to_small_embed(launch, "**Launch is in flight!**\n\n", pre_launch=False)
                await self.send_embeds(embed, bot_channels)

    async def check_ten_minute(self, bot_channels, time_threshold_10_minute, time_threshold_1_minute):
        logger.debug("Checking ten-minute launches...")
        ten_minute_launches = Launch.objects.filter(net__lte=time_threshold_10_minute,
                                                    net__gte=time_threshold_1_minute)
        for launch in ten_minute_launches:
            logger.debug("Found %s launches in the next ten minutes." % len(ten_minute_launches))
            notification, created = LaunchNotificationRecord.objects.get_or_create(launch_id=launch.id)
            if not notification.wasNotifiedTenMinutesDiscord:
                notification.wasNotifiedTenMinutesDiscord = True
                notification.save()
                logger.info("Ten Minutes - Launch Notification for %s" % launch.name)
                embed = launch_to_small_embed(launch, "**Launching in ten minutes!**\n\n")
                await self.send_embeds(embed, bot_channels)

    async def check_twenty_four_hour(self, bot_channels, time_threshold_1_hour, time_threshold_24_hour):
        logger.debug("Checking 24 hour launches...")
        twenty_four_hour_launches = Launch.objects.filter(net__lte=time_threshold_24_hour,
                                                          net__gte=time_threshold_1_hour)
        for launch in twenty_four_hour_launches:
            logger.debug("Found %s launches in the next 24 hours" % len(twenty_four_hour_launches))
            notification, created = LaunchNotificationRecord.objects.get_or_create(launch_id=launch.id)
            if not notification.wasNotifiedTwentyFourHourDiscord:
                notification.wasNotifiedTwentyFourHourDiscord = True
                notification.save()
                logger.info("Twenty Four Hour - Launch Notification for %s" % launch.name)
                embed = launch_to_small_embed(launch, "**Launching in twenty four hours!**\n\n")
                await self.send_embeds(embed, bot_channels)

    async def check_one_hour(self, bot_channels, time_threshold_10_minute, time_threshold_1_hour):
        logger.debug("Checking one hour launches...")
        one_hour_launches = Launch.objects.filter(net__lte=time_threshold_1_hour,
                                                  net__gte=time_threshold_10_minute)
        for launch in one_hour_launches:
            logger.debug("Found %s launches in the next hour." % len(one_hour_launches))
            notification, created = LaunchNotificationRecord.objects.get_or_create(launch_id=launch.id)
            if not notification.wasNotifiedOneHourDiscord:
                notification.wasNotifiedOneHourDiscord = True
                notification.save()
                logger.info("One Hour - Launch Notification for %s" % launch.name)
                embed = launch_to_small_embed(launch, "**Launching in one hour!**\n\n")
                await self.send_embeds(embed, bot_channels)

    async def check_webcast_live(self, bot_channels, time_threshold_1_hour, time_threshold_1_minute):
        logger.debug("Checking webcast live launches...")
        one_hour_launches = Launch.objects.filter(net__gte=time_threshold_1_minute, net__lte=time_threshold_1_hour,
                                                  webcast_live=True)
        for launch in one_hour_launches:
            logger.debug("Found %s launches with a live webcast." % len(one_hour_launches))
            notification, created = LaunchNotificationRecord.objects.get_or_create(launch_id=launch.id)
            if not notification.wasNotifiedWebcastDiscord:
                notification.wasNotifiedWebcastDiscord = True
                notification.save()
                logger.info("Webcast Live - Launch Notification for %s" % launch.name)
                embed = event_to_embed(launch, "**Webcast is live!**\n\n")
                await self.send_embeds(embed, bot_channels)

    async def check_webcast_live_event(self, bot_channels, time_threshold_1_hour, time_threshold_past_hour):
        logger.debug("Checking webcast live events...")
        events = Events.objects.filter(date__range=(time_threshold_past_hour, time_threshold_1_hour),
                                       webcast_live=True)
        for event in events:
            logger.debug("Found %s events with a live webcast." % len(events))
            if not event.was_discorded_webcast_live:
                event.was_discorded_webcast_live = True
                event.save()
                logger.info("Webcast Live - Event Notification for %s" % event.name)
                embed = event_to_embed(event, "**Webcast is live!**\n\n")
                await self.send_embeds(embed, bot_channels)

    async def check_ten_minute_event(self, bot_channels, time_threshold_10_minute, time_threshold_1_minute):
        logger.debug("Checking ten-minute events...")
        events = Events.objects.filter(date__lte=time_threshold_10_minute,
                                       date__gte=time_threshold_1_minute)
        for event in events:
            logger.debug("Found %s events in the next ten minutes." % len(events))
            if not event.was_discorded_ten_minutes:
                event.was_discorded_ten_minutes = True
                event.save()
                logger.info("Ten Minutes - Event Notification for %s" % event.name)
                embed = event_to_embed(event, "")
                await self.send_embeds(embed, bot_channels)

    async def send_embeds(self, embed, bot_channels):
        for bot_channel in bot_channels:
            logger.info("Sending notification to %s" % bot_channel.name)
            try:
                channel = self.bot.get_channel(int(bot_channel.channel_id))
                await channel.send(embed=embed)
            except Exception as e:
                logger.error(bot_channel.channel_id)
                logger.error(bot_channel.name)
                logger.error(e)
                if 'Missing Permissions' in e.args or 'Received NoneType' in e.args:
                    check_is_removed(bot_channel, e.args)
                continue

    @tasks.loop(seconds=60)
    async def discord_launch_events(self):
        bot_channels = DiscordChannel.objects.all()
        logger.info("Checking Discord launch events...")

        time_threshold_24_hour = datetime.datetime.now(tz=pytz.utc) + datetime.timedelta(hours=24)
        time_threshold_1_hour = datetime.datetime.now(tz=pytz.utc) + datetime.timedelta(hours=1)
        time_threshold_10_minute = datetime.datetime.now(tz=pytz.utc) + datetime.timedelta(minutes=10)
        time_threshold_1_minute = datetime.datetime.now(tz=pytz.utc) + datetime.timedelta(minutes=1)
        time_threshold_past_two_days = datetime.datetime.now(tz=pytz.utc) - datetime.timedelta(days=2)
        time_threshold_past_hour = datetime.datetime.now(tz=pytz.utc) - datetime.timedelta(hours=1)

        await self.check_twenty_four_hour(bot_channels, time_threshold_1_hour, time_threshold_24_hour)

        await self.check_one_hour(bot_channels, time_threshold_10_minute, time_threshold_1_hour)

        await self.check_ten_minute(bot_channels, time_threshold_10_minute, time_threshold_1_minute)

        await self.check_in_flight(bot_channels)

        await self.check_webcast_live(bot_channels, time_threshold_1_hour, time_threshold_1_minute)

        await self.check_success(bot_channels, time_threshold_past_two_days, time_threshold_24_hour)

        await self.check_ten_minute_event(bot_channels, time_threshold_10_minute, time_threshold_1_minute)

        await self.check_webcast_live_event(bot_channels, time_threshold_1_hour, time_threshold_past_hour)

        logger.info("Completed.")

    @tasks.loop(seconds=10)
    async def set_bot_description(self):
        logger.info("Updating Space Launch Bot's description.")
        message = ""
        global message_number
        message_number += 1
        try:
            if message_number == 1:
                message = ".sln help"
                await self.bot.change_presence(activity=discord.Activity(name=message,
                                                                         type=discord.ActivityType.listening))
            elif message_number == 2:
                member_count = 0
                for server in self.bot.guilds:
                    if server.id != 264445053596991498:
                        member_count += server.member_count
                message = "%s users in %s servers." % (member_count, len(self.bot.guilds))
                await self.bot.change_presence(activity=discord.Activity(name=message,
                                                                         type=discord.ActivityType.listening))
            elif message_number == 3:
                message = "with the Space Launch Now app on iOS and Android!"
                await self.bot.change_presence(activity=discord.Game(name=message))
            else:
                launch = Launch.objects.filter(net__gte=datetime.datetime.utcnow()).order_by('net').first()
                launch_date = launch.net
                now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
                message = u"""
                %s in %s. 
                """ % (launch.rocket.configuration.name, defaultfilters.timeuntil(launch_date, now))
                message_number = 0
                await self.bot.change_presence(activity=discord.Activity(name=message,
                                                                         large_image_url=launch.infographic_url,
                                                                         type=discord.ActivityType.watching),
                                               status=discord.Status.online,
                                               afk=False)
            logger.info("Done setting Space Launch Bot's description.")
        except Exception as e:
            logger.error(e)

    @discord_launch_events.before_loop
    @set_bot_description.before_loop
    async def before_loops(self):
        logger.info("Waiting for startup... (notifiers)")
        await self.bot.wait_until_ready()


def setup(bot):
    notification = Notifications(bot)
    bot.add_cog(notification)
