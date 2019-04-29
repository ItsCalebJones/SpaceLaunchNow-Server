import asyncio
import datetime
import logging
import time

import discord
import pytz
from discord import Colour
from discord.ext import commands
from twitter import Twitter, OAuth, TwitterError

from bot.models import Tweet, TwitterUser, TwitterNotificationChannel
from bot.utils import config

twitter = Twitter(auth=OAuth(consumer_key=config.keys['CONSUMER_KEY'],
                             consumer_secret=config.keys['CONSUMER_SECRET'],
                             token=config.keys['TOKEN_KEY'],
                             token_secret=config.keys['TOKEN_SECRET']))

logger = logging.getLogger('bot.discord')

def get_new_tweets():
    tweets = twitter.lists.statuses(owner_screen_name="spacelaunchnow",
                                    slug="space-launch-news",
                                    tweet_mode='extended')
    for tweet in tweets:
        userObj, created = TwitterUser.objects.get_or_create(user_id=tweet['user']['id'])
        userObj.default = True
        userObj.screen_name = tweet['user']['screen_name']
        userObj.name = tweet['user']['name']
        userObj.profile_image = tweet['user']['profile_image_url_https']
        userObj.save()
        tweetObj, created = Tweet.objects.get_or_create(id=tweet['id'], user=userObj)
        if created:
            logger.info("Found new tweet - %s" % tweet)
            tweetObj.text = tweet['full_text']
            tweetObj.default = True
            time_struct = time.strptime(tweet['created_at'], "%a %b %d %H:%M:%S +0000 %Y")
            date = datetime.datetime.fromtimestamp(time.mktime(time_struct))
            date = date.replace(tzinfo=pytz.utc)
            tweetObj.created_at = date
            tweetObj.user = userObj
            tweetObj.save()
    users = TwitterUser.objects.filter(custom=True)
    for user in users:
        tweets = twitter.statuses.user_timeline(screen_name=user.screen_name, count=5, tweet_mode='extended')
        for tweet in tweets:
            userObj, created = TwitterUser.objects.get_or_create(user_id=tweet['user']['id'])
            if created:
                break
            tweetObj, created = Tweet.objects.get_or_create(id=tweet['id'], user=userObj)
            if created:
                tweetObj.text = tweet['full_text']
                time_struct = time.strptime(tweet['created_at'], "%a %b %d %H:%M:%S +0000 %Y")
                date = datetime.datetime.fromtimestamp(time.mktime(time_struct))
                date = date.replace(tzinfo=pytz.utc)
                tweetObj.created_at = date
                tweetObj.save()


class Twitter:
    bot = None

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='addSpaceLaunchNews', pass_context=True)
    async def add_default_twitter_list(self, context):
        """Subscribe to the Space Launch New's Twitter list.

        https://twitter.com/SpaceLaunchNow/lists/space-launch-news

        Usage: ?addSpaceLaunchNews

        """
        try:
            owner_id = context.message.server.owner_id
            author_id = context.message.author.id
        except:
            await self.bot.send_message(context.message.channel, "Only able to run from a server channel.")
            return
        if owner_id == author_id:
            channel, created = TwitterNotificationChannel.objects.get_or_create(name=context.message.channel.name,
                                                                                channel_id=context.message.channel.id,
                                                                                server_id=context.message.server.id)
            channel.default_subscribed = True
            channel.save()
            await self.bot.send_message(context.message.channel, "Subscribed to Space Launch News!")
        else:
            await self.bot.send_message(context.message.channel,
                                        "Only server owners can add Twitter notification channels.")

    @commands.command(name='removeSpaceLaunchNews', pass_context=True)
    async def remove_default_twitter_list(self, context):
        """Unsubscribe from the Space Launch New's Twitter list.

        Usage: ?removeSpaceLaunchNews

        """
        try:
            owner_id = context.message.server.owner_id
            author_id = context.message.author.id
        except:
            await self.bot.send_message(context.message.channel, "Only able to run from a server channel.")
            return
        if owner_id == author_id:
            channel, created = TwitterNotificationChannel.objects.get_or_create(name=context.message.channel.name,
                                                                                channel_id=context.message.channel.id,
                                                                                server_id=context.message.server.id)
            channel.default_subscribed = False
            channel.save()
            await self.bot.send_message(context.message.channel, "Un-subscribed from Space Launch News!")
        else:
            await self.bot.send_message(context.message.channel,
                                        "Only server owners can add Twitter notification channels.")

    @commands.command(name='addTwitterUsername', pass_context=True)
    async def add_twitter_username(self, context, user):
        """Add a custom Twitter account for notifications.

        Usage: ?addTwitterUsername "<username>"

        Examples: ?addTwitterUsername "elonmusk"

        """
        user = user.lower()
        if ' ' in user:
            await self.bot.send_message(context.message.channel, "No spaces in Twitter usernames!")
            return
        try:
            owner_id = context.message.server.owner_id
            author_id = context.message.author.id
        except:
            await self.bot.send_message(context.message.channel, "Only able to run from a server channel.")
            return
        if owner_id == author_id:
            channel, created = TwitterNotificationChannel.objects.get_or_create(name=context.message.channel.name,
                                                                                channel_id=context.message.channel.id,
                                                                                server_id=context.message.server.id)
            channel.save()
            await self.add_notification(screen_name=user, discord_channel=channel)
        else:
            await self.bot.send_message(context.message.channel,
                                        "Only server owners can add Twitter notification channels.")

    @commands.command(name='removeTwitterUsername', pass_context=True)
    async def remove_username(self, context, user):
        """Remove custom Twitter account from notifications.

        Usage: ?removeTwitterUsername "<username>"

        Examples: ?removeTwitterUsername "elonmusk"

        """
        user = user.lower()
        if ' ' in user:
            await self.bot.send_message(context.message.channel, "No spaces in Twitter usernames!")
            return
        try:
            owner_id = context.message.server.owner_id
            author_id = context.message.author.id
        except:
            await self.bot.send_message(context.message.channel, "Only able to run from a server channel.")
            return
        if owner_id == author_id:
            channel, created = TwitterNotificationChannel.objects.get_or_create(name=context.message.channel.name,
                                                                                channel_id=context.message.channel.id,
                                                                                server_id=context.message.server.id)
            channel.save()
            await self.remove_notification(screen_name=user, discord_channel=channel)
        else:
            await self.bot.send_message(context.message.channel,
                                        "Only server owners can add Twitter notification channels.")

    @commands.command(name='listTwitterSubscriptions', pass_context=True)
    async def list_username(self, context):
        """List custom Twitter accounts.

        Usage: ?listTwitterSubscriptions

        """
        try:
            owner_id = context.message.server.owner_id
            author_id = context.message.author.id
        except:
            await self.bot.send_message(context.message.channel, "Only able to run from a server channel.")
            return
        if owner_id == author_id:
            channel, created = TwitterNotificationChannel.objects.get_or_create(name=context.message.channel.name,
                                                                                channel_id=context.message.channel.id,
                                                                                server_id=context.message.server.id)
            channel.save()
            await self.list_notification(discord_channel=channel)

    async def list_notification(self, discord_channel):
        try:
            users = TwitterUser.objects.filter(subscribers__channel_id=discord_channel.channel_id)
        except TwitterUser.DoesNotExist:
            users = None
        if users is None or len(users) == 0:
            await self.bot.send_message(self.bot.get_channel(id=discord_channel.channel_id),
                                        "Not subscribed to any custom Twitter accounts in this channel.")
        else:
            description = 'Custom Twitter Subscriptions: \n\n'
            for user in users:
                description += '%s (@%s)\n' % (user.name, user.screen_name)
            await self.bot.send_message(self.bot.get_channel(id=discord_channel.channel_id), description)

    async def remove_notification(self, screen_name, discord_channel):
        try:
            user = TwitterUser.objects.get(screen_name=screen_name)
        except TwitterUser.DoesNotExist:
            user = None
        if user is None:
            await self.bot.send_message(self.bot.get_channel(id=discord_channel.channel_id),
                                        "Not subscribed to %s in this channel." % screen_name)
        else:
            if len(TwitterUser.objects.filter(subscribers__in=[discord_channel])) > 0:
                user.subscribers.remove(discord_channel)
                if len(user.subscribers.all()) == 0:
                    user.delete()
                else:
                    user.save()
                await self.bot.send_message(self.bot.get_channel(id=discord_channel.channel_id),
                                            "Unsubscribed from %s in this channel." % screen_name)
            else:
                await self.bot.send_message(self.bot.get_channel(id=discord_channel.channel_id),
                                            "Not subscribed to %s in this channel." % screen_name)

    async def twitter_events(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed:
            try:
                await asyncio.wait_for(self.check_tweets(), 30)
            except Exception as e:
                logger.error(e)
            await asyncio.sleep(5)

    async def add_notification(self, screen_name, discord_channel):
        tweets = None
        userObj = None
        tweetObj = None
        try:
            tweets = twitter.statuses.user_timeline(screen_name=screen_name, count=5)
        except TwitterError:
            await self.bot.send_message(self.bot.get_channel(id=discord_channel.channel_id),
                                        'Error: User Doesn\'t Exist')
            return
        userObj, created = TwitterUser.objects.get_or_create(user_id=tweets[0]['user']['id'])
        if len(userObj.subscribers.all().filter(channel_id=discord_channel.channel_id)) > 0:
            await self.bot.send_message(self.bot.get_channel(id=discord_channel.channel_id),
                                        'Already subscribed to %s in this channel.' % screen_name)
            return
        if not userObj.default:
            userObj.custom = True
        userObj.screen_name = tweets[0]['user']['screen_name']
        userObj.name = tweets[0]['user']['name']
        userObj.profile_image = tweets[0]['user']['profile_image_url_https']
        userObj.subscribers.add(discord_channel)
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
        await self.bot.send_message(self.bot.get_channel(id=discord_channel.channel_id),
                                    'Subscribed to %s - here\'s the last tweet:' % userObj.name,
                                    embed=tweet_to_embed(userObj.tweets.order_by('created_at').first()))

    async def check_tweets(self):
        created_window = datetime.datetime.now(tz=pytz.utc) - datetime.timedelta(minutes=5)
        tweets = Tweet.objects.filter(read=False).filter(created_at__gte=created_window).order_by('created_at')
        for tweet in tweets:
            tweet.read = True
            tweet.save()
            if tweet.user.subscribers is not None:
                logger.info("Reading tweet from @%s" % tweet.user.name)
                for channel in tweet.user.subscribers.all():
                    logger.info("Sending to %s" % channel.name)
                    await self.bot.send_message(self.bot.get_channel(id=channel.channel_id), embed=tweet_to_embed(tweet))
            if tweet.default:
                logger.info("Default! Tweet from @%s" % tweet.user.name)
                for channel in TwitterNotificationChannel.objects.filter(default_subscribed=True):
                    logger.info("Sending to %s" % channel.name)
                    try:
                        await self.bot.send_message(self.bot.get_channel(id=channel.channel_id),
                                                    embed=tweet_to_embed(tweet))
                    except Exception as e:
                        if 'Missing Permissions' in e:
                            channel.delete()
                        logger.error(channel.id)
                        logger.error(channel.name)
                        logger.error(e)


def tweet_to_embed(tweet):
    title = "New Tweet by %s" % tweet.user.name
    color = Colour.green()
    embed = discord.Embed(type="rich", title=title,
                          description=tweet.text,
                          color=color,
                          url="https://twitter.com/statuses/%s" % tweet.id)
    embed.add_field(name="Twitter Link", value="https://twitter.com/statuses/%s" % tweet.id, inline=True)
    embed.set_thumbnail(url=tweet.user.profile_image)
    embed.set_footer(text=tweet.created_at.strftime("%A %B %e, %Y %H:%M %Z"))
    return embed


def setup(bot):
    twitter_bot = Twitter(bot)
    bot.add_cog(twitter_bot)
    bot.loop.create_task(twitter_bot.twitter_events())
