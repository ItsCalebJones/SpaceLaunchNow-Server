import asyncio
import datetime
import logging
import time

import discord
import pytz
from discord import Colour
from discord.ext import tasks, commands
from twitter import Twitter, OAuth, TwitterError

from bot.discord.utils import send_to_channel
from bot.models import Tweet, TwitterUser, TwitterNotificationChannel
from spacelaunchnow import config

twitter = Twitter(auth=OAuth(consumer_key=config.keys['CONSUMER_KEY'],
                             consumer_secret=config.keys['CONSUMER_SECRET'],
                             token=config.keys['TOKEN_KEY'],
                             token_secret=config.keys['TOKEN_SECRET']))

logger = logging.getLogger('bot.discord.tweets')


def check_is_removed(channel, args):
    logger.error("Unable to post to this channel: ")
    logger.error(channel)
    logger.error(args)


def tweet_to_embed(tweet):
    title = "New Tweet by %s" % tweet.user.name
    color = Colour.green()
    embed = discord.Embed(type="rich", title=title,
                          description=tweet.text,
                          color=color,
                          url="https://twitter.com/%s/status/%s" % (tweet.user.screen_name, tweet.id))
    embed.add_field(name="Twitter Link", value="https://twitter.com/%s/status/%s" % (tweet.user.screen_name, tweet.id),
                    inline=True)
    embed.set_thumbnail(url=tweet.user.profile_image)
    embed.set_footer(text=tweet.created_at.strftime("%A %B %e, %Y %H:%M %Z"))
    return embed


class Twitter(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.check_tweets.start()

    def cog_unload(self):
        self.check_tweets.cancel()

    @commands.command(name='addSpaceLaunchNews', pass_context=True)
    async def add_default_twitter_list(self, context):
        """Subscribe to the Space Launch New's Twitter list.

        https://twitter.com/SpaceLaunchNow/lists/space-launch-sync

        Usage: .sln addSpaceLaunchNews

        """
        channel = context.message.channel
        try:
            owner_id = context.message.guild.owner_id
            author_id = context.message.author.id
        except:
            await channel.send("Only able to run from a guild channel.")
            return
        if owner_id == author_id:
            notif_channel, created = TwitterNotificationChannel.objects.get_or_create(
                name=context.message.channel.name,
                channel_id=str(context.message.channel.id),
                server_id=str(context.message.guild.id)
            )
            notif_channel.default_subscribed = True
            notif_channel.save()
            await channel.send("Subscribed to Space Launch News!")
        else:
            await channel.send("Only server owners can add Twitter notification channels.")

    @commands.command(name='removeSpaceLaunchNews', pass_context=True)
    async def remove_default_twitter_list(self, context):
        """Unsubscribe from the Space Launch New's Twitter list.

        Usage: .sln removeSpaceLaunchNews

        """
        channel = context.message.channel
        try:
            owner_id = context.message.guild.owner_id
            author_id = context.message.author.id
        except:
            await channel.send("Only able to run from a server channel.")
            return
        if owner_id == author_id:
            notif_channel, created = TwitterNotificationChannel.objects.get_or_create(
                name=context.message.channel.name,
                channel_id=str(context.message.channel.id),
                server_id=str(context.message.guild.id)
            )
            notif_channel.default_subscribed = False
            notif_channel.save()
            await channel.send("Un-subscribed from Space Launch News!")
        else:
            await channel.send("Only server owners can add Twitter notification channels.")

    @commands.command(name='addTwitterUsername', pass_context=True)
    async def add_twitter_username(self, context, user):
        """Add a custom Twitter account for notifications.

        Usage: .sln addTwitterUsername "<username>"

        Examples: .sln addTwitterUsername "elonmusk"

        """
        channel = context.message.channel
        user = user.lower()
        if ' ' in user:
            await channel.send("No spaces in Twitter usernames!")
            return
        try:
            owner_id = context.message.guild.owner_id
            author_id = context.message.author.id
        except:
            await channel.send("Only able to run from a server channel.")
            return
        if owner_id == author_id:
            notif_channel, created = TwitterNotificationChannel.objects.get_or_create(
                name=context.message.channel.name,
                channel_id=str(context.message.channel.id),
                server_id=str(context.message.guild.id)
            )
            notif_channel.save()
            tweets = None
            userObj = None
            tweetObj = None
            try:
                tweets = twitter.statuses.user_timeline(screen_name=user, count=5)
            except TwitterError:
                await channel.send('Error: User Doesn\'t Exist')
                return
            userObj, created = TwitterUser.objects.get_or_create(user_id=tweets[0]['user']['id'])
            if len(userObj.subscribers.all().filter(channel_id=notif_channel.channel_id)) > 0:
                await channel.send('Already subscribed to %s in this channel.' % user)
                return
            if not userObj.default:
                userObj.custom = True
            userObj.screen_name = tweets[0]['user']['screen_name']
            userObj.name = tweets[0]['user']['name']
            userObj.profile_image = tweets[0]['user']['profile_image_url_https']
            userObj.subscribers.add(notif_channel)
            userObj.save()

            for tweet in tweets:
                tweetObj, created = Tweet.objects.get_or_create(id=tweet['id'], user=userObj, tweet_mode='extended')
                tweetObj.text = tweet['full_text']
                tweetObj.read = True
                time_struct = time.strptime(tweet['created_at'], "%a %b %d %H:%M:%S +0000 %Y")
                date = datetime.datetime.fromtimestamp(time.mktime(time_struct))
                date = date.replace(tzinfo=pytz.utc)
                tweetObj.created_at = date
                tweetObj.user = userObj
                tweetObj.save()
            await channel.send('Subscribed to %s - here\'s the last tweet:' % userObj.name,
                               embed=tweet_to_embed(userObj.tweets.order_by('created_at').first()))
        else:
            await channel.send("Only server owners can add Twitter notification channels.")

    @commands.command(name='removeTwitterUsername', pass_context=True)
    async def remove_username(self, context, user):
        """Remove custom Twitter account from notifications.

        Usage: .sln removeTwitterUsername "<username>"

        Examples: .sln removeTwitterUsername "elonmusk"

        """
        channel = context.message.channel
        user = user.lower()
        if ' ' in user:
            await channel.send("No spaces in Twitter usernames!")
            return
        try:
            owner_id = context.message.guild.owner_id
            author_id = context.message.author.id
        except:
            await channel.send("Only able to run from a server channel.")
            return
        if owner_id == author_id:
            notif_channel, created = TwitterNotificationChannel.objects.get_or_create(
                name=context.message.channel.name,
                channel_id=str(context.message.channel.id),
                server_id=str(context.message.guild.id)
            )
            notif_channel.save()
            try:
                user = TwitterUser.objects.get(screen_name=user)
            except TwitterUser.DoesNotExist:
                user = None
            if user is None:
                await channel.send("Not subscribed to %s in this channel." % user)
            else:
                if len(TwitterUser.objects.filter(subscribers__in=[notif_channel])) > 0:
                    user.subscribers.remove(notif_channel)
                    if len(user.subscribers.all()) == 0:
                        user.delete()
                    else:
                        user.save()
                    await channel.send("Unsubscribed from %s in this channel." % user)
                else:
                    await channel.send("Not subscribed to %s in this channel." % user)
        else:
            await channel.send("Only server owners can add Twitter notification channels.")

    @commands.command(name='listTwitterSubscriptions', pass_context=True)
    async def list_username(self, context):
        """List custom Twitter accounts.

        Usage: .sln listTwitterSubscriptions

        """
        channel = context.message.channel
        try:
            owner_id = context.message.guild.owner_id
            author_id = context.message.author.id
        except:
            await channel.send("Only able to run from a guild channel.")
            return
        if owner_id == author_id:
            notif_channel, created = TwitterNotificationChannel.objects.get_or_create(
                name=context.message.channel.name,
                channel_id=str(context.message.channel.id),
                server_id=str(context.message.guild.id)
            )
            notif_channel.save()
            try:
                users = TwitterUser.objects.filter(subscribers__channel_id=notif_channel.channel_id)
            except TwitterUser.DoesNotExist:
                users = None
            if users is None or len(users) == 0:
                await channel.send("Not subscribed to any custom Twitter accounts in this channel.")
            else:
                description = 'Custom Twitter Subscriptions: \n\n'
                for user in users:
                    description += '%s (@%s)\n' % (user.name, user.screen_name)
                await channel.send(description)

    @tasks.loop(minutes=1.0)
    async def check_tweets(self):
        logging.getLogger("asyncio").setLevel(logging.DEBUG)
        logger.debug("Checking unread tweets...")
        created_window = datetime.datetime.now(tz=pytz.utc) - datetime.timedelta(minutes=10)
        tweets = Tweet.objects.filter(read=False).filter(created_at__gte=created_window).order_by('created_at')
        for tweet in tweets:
            logger.info("Found %s unread tweets." % len(tweets))
            tweet.read = True
            tweet.save()
            if tweet.user.subscribers is not None:
                logger.info("Reading tweet from @%s" % tweet.user.name)
                for channel in tweet.user.subscribers.all():
                    await self.send_tweet(channel, tweet)
            if tweet.default:
                logger.info("Default! Tweet from @%s" % tweet.user.name)
                channels = TwitterNotificationChannel.objects.filter(default_subscribed=True)
                logger.info("Sending to %s channels" % len(channels))
                for channel in channels:
                    await self.send_tweet(channel, tweet)

    async def send_tweet(self, channel: TwitterNotificationChannel, tweet: Tweet) -> object:
        logger.info("Sending to channel %s-%s - (%s)" % (channel.id, channel.name, channel.server_id))
        try:
            discord_channel = self.bot.get_channel(id=int(channel.channel_id))
            embed = tweet_to_embed(tweet)
            await send_to_channel(discord_channel, channel, embed, logger)
        except Exception as e:
            logger.debug(channel.id)
            logger.error(e)
            if 'Missing Permissions' in e.args or 'Received NoneType' in e.args:
                check_is_removed(channel, e.args)
            return
        logger.info("Sent to %s successfully." % channel.id)

    @check_tweets.before_loop
    async def before_loops(self):
        logger.info("Waiting for startup... (twitter)")
        await self.bot.wait_until_ready()


def setup(bot):
    twitter_bot = Twitter(bot)
    bot.add_cog(twitter_bot)
