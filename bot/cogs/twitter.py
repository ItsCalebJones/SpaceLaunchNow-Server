import time

import discord
from discord import Colour
from discord.ext import commands
from twitter import Twitter, OAuth, TwitterError

from bot.models import Tweet, TwitterUser, DiscordChannel
from bot.utils import config

twitter = Twitter(auth=OAuth(consumer_key=config.keys['CONSUMER_KEY'],
                             consumer_secret=config.keys['CONSUMER_SECRET'],
                             token=config.keys['TOKEN_KEY'],
                             token_secret=config.keys['TOKEN_SECRET']))


class Social:
    bot = None

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='addTwitterUsername', pass_context=True)
    async def add_twitter_username(self, context, user):
        user = user.lower()
        try:
            owner_id = context.message.server.owner_id
            author_id = context.message.author.id
        except:
            await self.bot.send_message(context.message.channel, "Only able to run from a server channel.")
            return
        if owner_id == author_id:
            channel, created = DiscordChannel.objects.get_or_create(name=context.message.channel.name,
                                                                    channel_id=context.message.channel.id,
                                                                    server_id=context.message.server.id)
            channel.save()
            await self.add_notification(screen_name=user, discord_channel=channel)
        else:
            await self.bot.send_message(context.message.channel,
                                        "Only server owners can add Twitter notification channels.")

            # @commands.command(name='removeUsername', pass_context=True)
            # async def remove_username(self, context, user):
            #     user = user.lower()
            #     returned = remove_notification(screen_name=user, recipient_id=context.message.channel.id)
            #     await context.send(returned)

    async def add_notification(self, screen_name, discord_channel):
        try:
            tweets = twitter.statuses.user_timeline(screen_name=screen_name, count=5)
        except TwitterError:
            await self.bot.send_message(self.bot.get_channel(id=discord_channel.channel_id),
                                        'Error: User Doesn\'t Exist')
        userObj, created = TwitterUser.objects.get_or_create(user_id=tweets[0]['user']['id'])
        userObj.screen_name = tweets[0]['user']['screen_name']
        userObj.name = tweets[0]['user']['name']
        userObj.profile_image = tweets[0]['user']['profile_image_url_https']
        userObj.subscribers.add(discord_channel)
        userObj.save()

        for tweet in tweets:
            tweetObj, created = Tweet.objects.get_or_create(id=tweet['id'], user=userObj)
        tweetObj.text = tweet['text']
        tweetObj.created_at = time.strftime('%Y-%m-%d %H:%M:%S', time.strptime(tweet['created_at'],
                                                                               '%a %b %d %H:%M:%S +0000 %Y'))
        tweetObj.user = userObj
        tweetObj.save()
        await self.bot.send_message(self.bot.get_channel(id=discord_channel.channel_id),
                                    'Subscribed to %s - here\'s the last tweet:' % screen_name,
                                    embed=tweet_to_embed(userObj.tweets.order_by('created_at').first()))


def tweet_to_embed(tweet):
    title = "New Tweet by %s" % tweet.user.name
    color = Colour.green()
    embed = discord.Embed(type="rich", title=title,
                          description=tweet.text,
                          color=color,
                          url="https://twitter.com/statuses/%s" % tweet.id)
    embed.set_thumbnail(url=tweet.user.profile_image)
    return embed


# def purge_notifs(screen_name):
# user_exists = (TwitterNotification.objects.filter(twitter_user=screen_name)
#                .exists())
# if not user_exists:
#     Tweet.objects.filter(user=screen_name).delete()


# def add_tweets():
# users = (TwitterNotification.objects.order_by()
#          .values_list('twitter_user', flat=True).distinct())
#
# for user in users:
#     t = api.GetUserTimeline(screen_name=user, count=5)
#     tweets = [i.AsDict() for i in t]
#     for tweet in tweets:
#         Tweet.objects.get_or_create(id=tweet['id'],
#                                     user=tweet['user']['screen_name'],
#                                     text=tweet['text'])


# def remove_notification(screen_name, recipient_id):
# exists = (TwitterNotification.objects.filter(twitter_user=screen_name,
#                                              recipient_id=recipient_id)
#           .exists())
#
# if exists:
#     TwitterNotification.objects.filter(twitter_user=screen_name,
#                                        recipient_id=recipient_id).delete()
#     purge_notifs(screen_name)
#     return 'Success'
# else:
#     return 'No Such Notification'


def setup(bot):
    bot.add_cog(Social(bot))
