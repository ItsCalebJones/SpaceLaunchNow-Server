import logging

import discord
from discord import Colour
from discord.ext import tasks, commands
from prawcore import Redirect
from twitter import Twitter, OAuth

from bot.app.sync.reddit_sync import get_posts_by_subreddit
from bot.discord.utils import send_to_channel
from spacelaunchnow import config
from bot.models import SubredditNotificationChannel, Subreddit, RedditSubmission

import praw

user_agent = 'Space Launch News Bot'
reddit = praw.Reddit(client_id=config.REDDIT_CLIENT_ID,
                     client_secret=config.REDDIT_CLIENT_SECRET,
                     user_agent=config.REDDIT_AGENT, )

reddit.read_only = True

twitter = Twitter(auth=OAuth(consumer_key=config.keys['CONSUMER_KEY'],
                             consumer_secret=config.keys['CONSUMER_SECRET'],
                             token=config.keys['TOKEN_KEY'],
                             token_secret=config.keys['TOKEN_SECRET']))

logger = logging.getLogger('bot.discord')


def check_is_removed(channel, args):
    logger.error("Unable to post to this channel: ")
    logger.error(channel)
    logger.error(args)


def submission_to_embed(submission):
    title = "New Hot Submission in /r/%s by /u/%s" % (submission.subreddit.name, submission.user)
    color = Colour.red()
    description = "[%s](https://reddit.com%s)" % (submission.title, submission.permalink)

    embed = discord.Embed(type="rich", title=title,
                          color=color,
                          description=description)

    if submission.selftext:
        text = (submission.text[:400] + '...') if len(submission.text) > 400 else submission.text
        embed.add_field(name="Self Text", value=text, inline=True)
    else:
        if "twitter.com" in submission.link:
            try:
                link = submission.link.split('/')[-1]
                link = link.split('?')[0]
                status = twitter.statuses.show(id=link)

                embed.add_field(name="Tweet", value="\"%s\" - %s" % (status['text'], status['user']['name']),
                                inline=True)
            except Exception as e:
                logger.error(e)
        elif submission.text is not None:
            try:
                embed.add_field(name="Link Summary", value=submission.text, inline=True)
            except Exception as e:
                logger.error(e)

    if submission.thumbnail is not None and submission.thumbnail != 'self' and submission.thumbnail != 'default':
        embed.set_thumbnail(url=submission.thumbnail)
    else:
        embed.set_thumbnail(url="https://i.redd.it/rq36kl1xjxr01.png")
    embed.add_field(name="Comments", value="https://reddit.com%s" % submission.permalink, inline=True)
    embed.set_footer(text="Score: %s • Comments: %s" % (submission.score, submission.comments))
    return embed


class Reddit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_submissions.start()

    def cog_unload(self):
        self.check_submissions.cancel()

    @commands.command(name='addSubreddit', pass_context=True)
    async def add_reddit(self, context, subreddit):
        """Add notifications for new subreddit posts.

        Usage: .sln addSubreddit "<subreddit>"

        Examples: .sln  addSubreddit spacex

        """
        subreddit = subreddit.lower()
        channel = context.message.channel
        if ' ' in subreddit:
            await self.bot.send_message(context.message.channel, "No spaces in Twitter usernames!")
            return
        try:
            owner_id = context.message.guild.owner_id
            author_id = context.message.author.id
        except:
            await channel.send("Only able to run from a guild channel.")
            return
        if owner_id == author_id:
            notif_channel, created = SubredditNotificationChannel.objects.get_or_create(
                name=context.message.channel.name,
                channel_id=str(context.message.channel.id),
                server_id=str(context.message.guild.id))
            notif_channel.save()
            await self.add_subreddit(subreddit_name=subreddit, channel=channel, notif_channel=notif_channel)
        else:
            await channel.send("Only guild owners can add Twitter notification channels.")

    @commands.command(name='removeSubreddit', pass_context=True)
    async def remove_reddit(self, context, subreddit):
        """Remove notifications for new subreddit posts.

        Usage: .sln removeSubreddit "<subreddit>"

        Examples: .sln  removeSubreddit spacex

        """
        subreddit = subreddit.lower()
        channel = context.message.channel
        logger.info("Hello")
        if ' ' in subreddit:
            await channel.send("No spaces in Subreddit names!")
            return
        try:
            owner_id = context.message.guild.owner_id
            author_id = context.message.author.id
        except:
            await channel.send("Only able to run from a guild channel.")
            return
        logger.info("sir")
        if owner_id == author_id:
            logger.info("sir")
            notif_channel, created = SubredditNotificationChannel.objects.get_or_create(
                name=context.message.channel.name,
                channel_id=str(context.message.channel.id),
                server_id=str(context.message.guild.id))
            notif_channel.save()
            logger.info(notif_channel)
            await self.remove_subreddit(subreddit_name=subreddit, channel=channel, notif_channel=notif_channel)
        else:
            await channel.send("Only guild owners can add Twitter notification channels.")

    @commands.command(name='listSubreddits', pass_context=True)
    async def list_username(self, context):
        """List subscribed Sub-reddits.

        Usage: .sln listSubreddits

        """
        channel = context.message.channel
        try:
            owner_id = context.message.guild.owner_id
            author_id = context.message.author.id
        except:
            await channel.send("Only able to run from a guild channel.")
            return
        if owner_id == author_id:
            notif_channel, created = SubredditNotificationChannel.objects.get_or_create(
                name=context.message.channel.name,
                channel_id=str(context.message.channel.id),
                server_id=str(context.message.guild.id))
            notif_channel.save()
            await self.list_subreddit(channel=channel, notif_channel=notif_channel)

    async def list_subreddit(self, channel, notif_channel):
        try:
            subreddits = Subreddit.objects.filter(subscribers__channel_id=notif_channel.channel_id)
        except Subreddit.DoesNotExist:
            subreddits = None
        if subreddits is None or len(subreddits) == 0:
            await channel.send("Not subscribed to any subreddits in this channel.")
        else:
            description = 'Subreddit Subscriptions: \n\n'
            for subreddit in subreddits:
                description += '/r/%s\n' % subreddit.name
            await channel.send(description)

    async def add_subreddit(self, subreddit_name, channel, notif_channel):
        try:
            for submission in reddit.subreddit(subreddit_name).hot(limit=1):
                subreddit, created = Subreddit.objects.get_or_create(id=submission.subreddit.id)
                subreddit.name = submission.subreddit.display_name
                if subreddit.subscribers is not None and len(
                        subreddit.subscribers.all().filter(channel_id=notif_channel.channel_id)) > 0:
                    if channel is None or not channel.guild.me.permissions_in(channel).send_messages:
                        pass
                    await channel.send('Already subscribed to /r/%s in this channel.' % subreddit_name)
                    return
                else:
                    subreddit.subscribers.add(notif_channel)
                    subreddit.save()
                    if not subreddit.initialized:
                        if channel is None or not channel.guild.me.permissions_in(channel).send_messages:
                            pass
                        await channel.send("Checking...one sec!")
                        async with channel.typing():
                            get_posts_by_subreddit(subreddit, mark_read=True)
                            subreddit.initialized = True
                    subreddit.save()
                    if channel is None or not channel.guild.me.permissions_in(channel).send_messages:
                        pass
                    await channel.send("Subscribed to /r/%s in this channel.\n\n"
                                       "Here's the latest Hot post:\n" % subreddit_name,
                                       embed=submission_to_embed(
                                           subreddit.submissions.order_by('created_at').first()))
        except Redirect as e:
            if channel is None or not channel.guild.me.permissions_in(channel).send_messages:
                pass
            await channel.send("Subreddit doesn't exist.")

    async def remove_subreddit(self, subreddit_name, channel,  notif_channel):
        logger.info("blah")
        try:
            subreddit = Subreddit.objects.get(name=subreddit_name)
        except Subreddit.DoesNotExist:
            subreddit = None
        if subreddit is None:
            await channel.send("Not subscribed to /r/%s in this channel." % subreddit_name)
        else:
            if len(Subreddit.objects.filter(subscribers__in=[notif_channel])) > 0:
                subreddit.subscribers.remove(notif_channel)
                if len(subreddit.subscribers.all()) == 0:
                    subreddit.delete()
                else:
                    subreddit.save()
                await channel.send("Unsubscribed from /r/%s in this channel." % subreddit_name)
            else:
                await channel.send("Not subscribed to /r/%s in this channel." % subreddit_name)

    @tasks.loop(minutes=5)
    async def check_submissions(self):
        logger.debug("Checking for submissions.")
        submissions = RedditSubmission.objects.filter(read=False)
        for submission in submissions:
            logger.info("Found %s submissions to read." % len(submissions))
            submission.read = True
            submission.save()
            if submission.subreddit.subscribers is not None:
                for channel in submission.subreddit.subscribers.all():
                    logger.info("Sending %s to %s - %s" % (submission.id, channel.id, channel.name))
                    try:
                        embed = submission_to_embed(submission)
                        discord_channel = self.bot.get_channel(id=int(channel.channel_id))
                        await send_to_channel(discord_channel, channel, embed, logger)
                    except Exception as e:
                        logger.error(channel.id)
                        logger.error(channel.name)
                        logger.error(e)
                        if 'Missing Permissions' in e.args or 'Received NoneType' in e.args:
                            check_is_removed(channel, e.args)
                        continue

    @check_submissions.before_loop
    async def before_loops(self):
        logger.info("Waiting for startup... (reddit)")
        await self.bot.wait_until_ready()


def setup(bot):
    reddit_bot = Reddit(bot)
    bot.add_cog(reddit_bot)
