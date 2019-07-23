import datetime
import asyncio
import logging

import discord
import pytz
from discord.ext import commands
from django.db.models import Q
from django.template import defaultfilters

from api.models import Launch, Events
from bot.cogs.launches import launch_to_small_embed, event_to_embed
from bot.models import DiscordChannel, Notification

logger = logging.getLogger('bot.discord.notifications')


class Notifications:
    def __init__(self, bot):
        self.bot = bot
        self.description = 120

    @commands.command(pass_context=True)
    async def addNotificationChannel(self, context):
        """Subscribe current channel to launch notifications.

        Note: Only server owners can perform this action.

        Usage: ?addNotificationChannel
        """
        try:
            ownerid = context.message.server.owner_id
            authorid = context.message.author.id
        except:
            await self.bot.send_message(context.message.channel, "Only able to run from a server channel.")
            return
        if ownerid == authorid:
            channel = DiscordChannel(name=context.message.channel.name,
                                     channel_id=context.message.channel.id,
                                     server_id=context.message.server.id)
            channel.save()
            await self.bot.send_message(context.message.channel,
                                        "Added this channel to notification list.")
        else:
            await self.bot.send_message(context.message.channel,
                                        "Only server owners can add notification channels.")

    @commands.command(pass_context=True)
    async def removeNotificationChannel(self, context):
        """Remove current channel from launch notifications.

        Note: Only server owners can perform this action.

        Usage: ?removeNotificationChannel
        """
        try:
            ownerid = context.message.server.owner_id
            authorid = context.message.author.id
        except:
            await self.bot.send_message(context.message.channel, "Only able to run from a server channel.")
            return
        if ownerid == authorid:
            channel = DiscordChannel.objects.filter(server_id=context.message.server.id,
                                                    channel_id=context.message.channel.id).first()
            channel.delete()
            await self.bot.send_message(context.message.channel,
                                        "Removed this channel from the notification list.")
        else:
            await self.bot.send_message(context.message.channel,
                                        "Only server owners can remove notification channels.")

    @commands.command(pass_context=True)
    async def listNotificationChannels(self, context):
        """List all channels that are subscribed to launch notifications.

        Note: Only server owners can perform this action.

        Usage: ?listNotificationChannels
        """
        try:
            ownerid = context.message.server.owner_id
            authorid = context.message.author.id
        except:
            await self.bot.send_message(context.message.channel, "Only able to run from a server channel.")
            return
        if ownerid == authorid:
            channels = DiscordChannel.objects.filter(server_id=context.message.server.id)
            channel_text = "**Here ya go %s!**" % context.message.author.name
            for channel in channels:
                channel_text = channel_text + "\n* %s" % channel.name
            channel_text = channel_text + "\n\nUse ?help for help managing notifications."
            await self.bot.send_message(context.message.channel, channel_text)
        else:
            await self.bot.send_message(context.message.channel, "Only server owners list notification channels.")

    async def check_success(self, bot_channels, time_threshold_past_two_days, time_threshold_24_hour):
        logger.debug("Checking successful launches...")
        recent_success_launches = Launch.objects.filter(Q(status__id=3) | Q(status__id=4) | Q(status__id=7),
                                                        net__lte=time_threshold_24_hour,
                                                        net__gte=time_threshold_past_two_days)
        for launch in recent_success_launches:
            logger.debug("Found %s successful launches" % len(recent_success_launches))
            notification, created = Notification.objects.get_or_create(launch=launch)
            if not notification.wasNotifiedSuccessDiscord:
                notification.wasNotifiedSuccessDiscord = True
                notification.save()
                logger.info("Success - Launch Notification for %s" % launch.name)
                for channel in bot_channels:
                    logger.info("Sending notification to %s" % channel.name)
                    try:
                        await self.bot.send_message(channel,
                                                    embed=launch_to_small_embed(launch,
                                                                                "**Launch was a %s!**\n\n" % launch.status.name,
                                                                                pre_launch=False))
                    except Exception as e:
                        logger.error(channel.id)
                        logger.error(channel.name)
                        logger.error(e)
                        if 'Missing Permissions' in e.args or 'Received NoneType' in e.args:
                            channel.delete()
                        return

    async def check_in_flight(self, bot_channels):
        logger.debug("Checking in-flight launches...")
        in_flight_launches = Launch.objects.filter(status__id=6)
        for launch in in_flight_launches:
            logger.debug("Found %s in flight launches" % len(in_flight_launches))
            notification, created = Notification.objects.get_or_create(launch=launch)
            if not notification.wasNotifiedInFlightDiscord:
                notification.wasNotifiedInFlightDiscord = True
                notification.save()
                logger.info("In-Flight - Launch Notification for %s" % launch.name)
                for channel in bot_channels:
                    logger.info("Sending notification to %s" % channel.name)
                    try:
                        await self.bot.send_message(channel,
                                                    embed=launch_to_small_embed(launch, "**Launch is in flight!**\n\n",
                                                                                pre_launch=False))
                    except Exception as e:
                        logger.error(channel.id)
                        logger.error(channel.name)
                        logger.error(e)
                        if 'Missing Permissions' in e.args or 'Received NoneType' in e.args:
                            channel.delete()
                        return

    async def check_one_minute(self, bot_channels, time_threshold_1_minute):
        logger.debug("Checking one-minute launches...")
        one_minute_launches = Launch.objects.filter(net__lte=time_threshold_1_minute,
                                                    net__gte=datetime.datetime.now(tz=pytz.utc))
        for launch in one_minute_launches:
            logger.debug("Found %s launches in the next minute." % len(one_minute_launches))
            notification, created = Notification.objects.get_or_create(launch=launch)
            if not notification.wasNotifiedOneMinutesDiscord:
                notification.wasNotifiedOneMinutesDiscord = True
                notification.save()
                logger.info("One Minute - Launch Notification for %s" % launch.name)
                for channel in bot_channels:
                    logger.info("Sending notification to %s" % channel.name)
                    try:
                        await self.bot.send_message(channel,
                                                    embed=launch_to_small_embed(launch,
                                                                                "**Launching in one minute!**\n\n"))
                    except Exception as e:
                        logger.error(channel.id)
                        logger.error(channel.name)
                        logger.error(e)
                        if 'Missing Permissions' in e.args or 'Received NoneType' in e.args:
                            channel.delete()
                        return

    async def check_ten_minute(self, bot_channels, time_threshold_10_minute, time_threshold_1_minute):
        logger.debug("Checking ten-minute launches...")
        ten_minute_launches = Launch.objects.filter(net__lte=time_threshold_10_minute,
                                                    net__gte=time_threshold_1_minute)
        for launch in ten_minute_launches:
            logger.debug("Found %s launches in the next ten minutes." % len(ten_minute_launches))
            notification, created = Notification.objects.get_or_create(launch=launch)
            if not notification.wasNotifiedTenMinutesDiscord:
                notification.wasNotifiedTenMinutesDiscord = True
                notification.save()
                logger.info("Ten Minutes - Launch Notification for %s" % launch.name)
                for channel in bot_channels:
                    logger.info("Sending notification to %s" % channel.name)
                    try:
                        await self.bot.send_message(channel,
                                                    embed=launch_to_small_embed(launch,
                                                                                "**Launching in ten minutes!**\n\n"))
                    except Exception as e:
                        logger.error(channel.id)
                        logger.error(channel.name)
                        logger.error(e)
                        if 'Missing Permissions' in e.args or 'Received NoneType' in e.args:
                            channel.delete()
                        return

    async def check_twenty_four_hour(self, bot_channels, time_threshold_1_hour, time_threshold_24_hour):
        logger.debug("Checking 24 hour launches...")
        twenty_four_hour_launches = Launch.objects.filter(net__lte=time_threshold_24_hour,
                                                          net__gte=time_threshold_1_hour)
        for launch in twenty_four_hour_launches:
            logger.debug("Found %s launches in the next 24 hours" % len(twenty_four_hour_launches))
            notification, created = Notification.objects.get_or_create(launch=launch)
            if not notification.wasNotifiedTwentyFourHourDiscord:
                notification.wasNotifiedTwentyFourHourDiscord = True
                notification.save()
                logger.info("Twenty Four Hour - Launch Notification for %s" % launch.name)
                for channel in bot_channels:
                    logger.info("Sending notification to %s" % channel.name)
                    try:
                        await self.bot.send_message(channel, embed=launch_to_small_embed(launch,
                                                                                         "**Launching in twenty four hours!**\n\n"))
                    except Exception as e:
                        logger.error(channel.id)
                        logger.error(channel.name)
                        logger.error(e)
                        if 'Missing Permissions' in e.args or 'Received NoneType' in e.args:
                            channel.delete()
                        return

    async def check_one_hour(self, bot_channels, time_threshold_10_minute, time_threshold_1_hour):
        logger.debug("Checking one hour launches...")
        one_hour_launches = Launch.objects.filter(net__lte=time_threshold_1_hour,
                                                  net__gte=time_threshold_10_minute)
        for launch in one_hour_launches:
            logger.debug("Found %s launches in the next hour." % len(one_hour_launches))
            notification, created = Notification.objects.get_or_create(launch=launch)
            if not notification.wasNotifiedOneHourDiscord:
                notification.wasNotifiedOneHourDiscord = True
                notification.save()
                logger.info("One Hour - Launch Notification for %s" % launch.name)
                for channel in bot_channels:
                    logger.info("Sending notification to %s" % channel.name)
                    try:
                        await self.bot.send_message(channel,
                                                    embed=launch_to_small_embed(launch,
                                                                                "**Launching in one hour!**\n\n"))
                    except Exception as e:
                        logger.error(channel.id)
                        logger.error(channel.name)
                        logger.error(e)
                        if 'Missing Permissions' in e.args or 'Received NoneType' in e.args:
                            channel.delete()
                        return

    async def check_webcast_live(self, bot_channels, time_threshold_1_hour, time_threshold_1_minute):
        logger.debug("Checking webcast live launches...")
        one_hour_launches = Launch.objects.filter(net__gte=time_threshold_1_minute, net__lte=time_threshold_1_hour,
                                                  webcast_live=True)
        for launch in one_hour_launches:
            logger.debug("Found %s launches with a live webcast." % len(one_hour_launches))
            notification, created = Notification.objects.get_or_create(launch=launch)
            if not notification.wasNotifiedWebcastDiscord:
                notification.wasNotifiedWebcastDiscord = True
                notification.save()
                logger.info("Webcast Live - Launch Notification for %s" % launch.name)
                for channel in bot_channels:
                    logger.info("Sending notification to %s" % channel.name)
                    try:
                        await self.bot.send_message(channel,
                                                    embed=event_to_embed(launch, "**Webcast is live!**\n\n"))
                    except Exception as e:
                        logger.error(channel.id)
                        logger.error(channel.name)
                        logger.error(e)
                        if 'Missing Permissions' in e.args or 'Received NoneType' in e.args:
                            channel.delete()
                        return

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
                for channel in bot_channels:
                    logger.info("Sending notification to %s" % channel.id)
                    try:
                        await self.bot.send_message(channel, embed=event_to_embed(event, "**Webcast is live!**\n\n"))
                    except Exception as e:
                        logger.error(channel.id)
                        logger.error(channel.name)
                        logger.error(e)
                        if 'Missing Permissions' in e.args or 'Received NoneType' in e.args:
                            channel.delete()
                        return

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
                for channel in bot_channels:
                    logger.info("Sending notification to %s" % channel.name)
                    try:
                        await self.bot.send_message(channel,
                                                    embed=event_to_embed(event,
                                                                         "**Launching in ten minutes!**\n\n"))
                    except Exception as e:
                        logger.error(channel.id)
                        logger.error(channel.name)
                        logger.error(e)
                        if 'Missing Permissions' in e.args or 'Received NoneType' in e.args:
                            channel.delete()
                        return

    async def discord_launch_events(self):
        await self.bot.wait_until_ready()
        channels = DiscordChannel.objects.all()
        bot_channels = []
        for channel in channels:
            discord_channel = self.bot.get_channel(id=channel.channel_id)
            if discord_channel is None or not discord_channel.server.me.permissions_in(discord_channel).send_messages:
                channel.delete()
            else:
                bot_channels.append(discord_channel)

        while not self.bot.is_closed:
            logger.debug("Checking Discord launch events...")
            time_threshold_24_hour = datetime.datetime.now(tz=pytz.utc) + datetime.timedelta(hours=24)
            time_threshold_1_hour = datetime.datetime.now(tz=pytz.utc) + datetime.timedelta(hours=1)
            time_threshold_10_minute = datetime.datetime.now(tz=pytz.utc) + datetime.timedelta(minutes=10)
            time_threshold_1_minute = datetime.datetime.now(tz=pytz.utc) + datetime.timedelta(minutes=1)
            time_threshold_past_two_days = datetime.datetime.now(tz=pytz.utc) - datetime.timedelta(days=2)
            time_threshold_past_hour = datetime.datetime.now(tz=pytz.utc) - datetime.timedelta(hours=1)

            await self.check_twenty_four_hour(bot_channels, time_threshold_1_hour, time_threshold_24_hour)

            await self.check_one_hour(bot_channels, time_threshold_10_minute, time_threshold_1_hour)

            await self.check_ten_minute(bot_channels, time_threshold_10_minute, time_threshold_1_minute)

            await self.check_one_minute(bot_channels, time_threshold_1_minute)

            await self.check_in_flight(bot_channels)

            await self.check_webcast_live(bot_channels, time_threshold_1_hour, time_threshold_1_minute)

            await self.check_success(bot_channels, time_threshold_past_two_days, time_threshold_24_hour)

            await self.check_ten_minute_event(bot_channels, time_threshold_10_minute, time_threshold_1_minute)

            await self.check_webcast_live_event(bot_channels, time_threshold_1_hour, time_threshold_past_hour)

            await self.set_bot_description()

            logger.debug("Completed.")
            await asyncio.sleep(30)

    async def set_bot_description(self):
        if self.description == 60:
            logger.info("Updating Space Launch Bot's description.")
            launch = Launch.objects.filter(net__gte=datetime.datetime.utcnow()).order_by('net').first()
            launch_date = launch.net
            now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
            message = u"""
            %s in %s. Use ?help for commands.
            """ % (launch.name, defaultfilters.timeuntil(launch_date, now))
            squid_bot_game = discord.Game(name=message, url=launch.get_full_absolute_url(), type=0)
            await self.bot.change_presence(game=squid_bot_game, status=discord.Status.online, afk=False)
            self.description = 0
        else:
            self.description += 1


def setup(bot):
    notification = Notifications(bot)
    bot.add_cog(notification)
    bot.loop.create_task(notification.discord_launch_events())
