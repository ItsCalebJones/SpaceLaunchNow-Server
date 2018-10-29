import datetime
import asyncio

import pytz
from discord.ext import commands
from django.db.models import Q

from api.models import Launch
from bot.cogs.launches import launch_to_small_embed
from bot.models import DiscordChannel, Notification

class Notifications:
    def __init__(self, bot):
        self.bot = bot

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
        recent_success_launches = Launch.objects.filter(Q(status__id=3) | Q(status__id=4) | Q(status__id=7),
                                                        net__lte=time_threshold_24_hour,
                                                        net__gte=time_threshold_past_two_days)
        for launch in recent_success_launches:
            notification, created = Notification.objects.get_or_create(launch=launch)
            if not notification.wasNotifiedSuccessDiscord:
                notification.wasNotifiedSuccessDiscord = True
                notification.save()
                for channel in bot_channels:
                    await self.bot.send_message(channel,
                                                embed=launch_to_small_embed(launch, "**Launch was a %s!**\n\n" % launch.status.name))

    async def check_in_flight(self, bot_channels):
        in_flight_launches = Launch.objects.filter(status__id=6)
        for launch in in_flight_launches:
            notification, created = Notification.objects.get_or_create(launch=launch)
            if not notification.wasNotifiedInFlightDiscord:
                notification.wasNotifiedInFlightDiscord = True
                notification.save()
                for channel in bot_channels:
                    await self.bot.send_message(channel,
                                                embed=launch_to_small_embed(launch, "**Launch is in flight!**\n\n"))

    async def check_one_minute(self, bot_channels, time_threshold_1_minute):
        one_minute_launches = Launch.objects.filter(net__lte=time_threshold_1_minute,
                                                    net__gte=datetime.datetime.now(tz=pytz.utc))
        for launch in one_minute_launches:
            notification, created = Notification.objects.get_or_create(launch=launch)
            if not notification.wasNotifiedOneMinutesDiscord:
                notification.wasNotifiedOneMinutesDiscord = True
                notification.save()
                for channel in bot_channels:
                    await self.bot.send_message(channel,
                                                embed=launch_to_small_embed(launch, "**Launching in one minute!**\n\n"))

    async def check_ten_minute(self, bot_channels, time_threshold_10_minute, time_threshold_1_minute):
        ten_minute_launches = Launch.objects.filter(net__lte=time_threshold_10_minute,
                                                    net__gte=time_threshold_1_minute)
        for launch in ten_minute_launches:
            notification, created = Notification.objects.get_or_create(launch=launch)
            if not notification.wasNotifiedTenMinutesDiscord:
                notification.wasNotifiedTenMinutesDiscord = True
                notification.save()
                for channel in bot_channels:
                    await self.bot.send_message(channel,
                                                embed=launch_to_small_embed(launch,
                                                                            "**Launching in ten minutes!**\n\n"))

    async def check_twenty_four_hour(self, bot_channels, time_threshold_1_hour, time_threshold_24_hour):
        twenty_four_hour_launches = Launch.objects.filter(net__lte=time_threshold_24_hour,
                                                          net__gte=time_threshold_1_hour)
        for launch in twenty_four_hour_launches:
            notification, created = Notification.objects.get_or_create(launch=launch)
            if not notification.wasNotifiedTwentyFourHourDiscord:
                notification.wasNotifiedTwentyFourHourDiscord = True
                notification.save()
                for channel in bot_channels:
                    await self.bot.send_message(channel, embed=launch_to_small_embed(launch,
                                                                                     "**Launching in twenty four hours!**\n\n"))

    async def check_one_hour(self, bot_channels, time_threshold_10_minute, time_threshold_1_hour):
        one_hour_launches = Launch.objects.filter(net__lte=time_threshold_1_hour,
                                                  net__gte=time_threshold_10_minute)
        for launch in one_hour_launches:
            notification, created = Notification.objects.get_or_create(launch=launch)
            if not notification.wasNotifiedOneHourDiscord:
                notification.wasNotifiedOneHourDiscord = True
                notification.save()
                for channel in bot_channels:
                    await self.bot.send_message(channel,
                                                embed=launch_to_small_embed(launch, "**Launching in one hour!**\n\n"))

    async def discord_launch_events(self):
        await self.bot.wait_until_ready()
        channels = DiscordChannel.objects.all()
        bot_channels = []
        for channel in channels:
            bot_channels.append(self.bot.get_channel(id=channel.channel_id))
        while not self.bot.is_closed:
            print("Checking launch windows!")
            time_threshold_24_hour = datetime.datetime.now(tz=pytz.utc) + datetime.timedelta(hours=24)
            time_threshold_1_hour = datetime.datetime.now(tz=pytz.utc) + datetime.timedelta(hours=1)
            time_threshold_10_minute = datetime.datetime.now(tz=pytz.utc) + datetime.timedelta(minutes=10)
            time_threshold_1_minute = datetime.datetime.now(tz=pytz.utc) + datetime.timedelta(minutes=1)
            time_threshold_past_two_days = datetime.datetime.now(tz=pytz.utc) - datetime.timedelta(days=2)

            await self.check_twenty_four_hour(bot_channels, time_threshold_1_hour, time_threshold_24_hour)

            await self.check_one_hour(bot_channels, time_threshold_10_minute, time_threshold_1_hour)

            await self.check_ten_minute(bot_channels, time_threshold_10_minute, time_threshold_1_minute)

            await self.check_one_minute(bot_channels, time_threshold_1_minute)

            await self.check_in_flight(bot_channels)

            await self.check_success(bot_channels, time_threshold_past_two_days, time_threshold_24_hour)

            await asyncio.sleep(10)


def setup(bot):
    notification = Notifications(bot)
    bot.add_cog(notification)
    bot.loop.create_task(notification.discord_launch_events())
