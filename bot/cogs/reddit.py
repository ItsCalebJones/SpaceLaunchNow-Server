import asyncio

import datetime
import logging

import discord
import prawcore
import pytz
from goose3 import Goose
from discord import Colour
from discord.ext import commands
from prawcore import Redirect
from twitter import Twitter, OAuth

from bot.models import SubredditNotificationChannel, Subreddit, RedditSubmission

import praw

from bot.utils import config

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


def get_submissions():
    logger.info("Getting Reddit submissions.")
    subreddits = Subreddit.objects.filter(initialized=True)
    for subreddit in subreddits:
        logger.debug("Getting submissions for /r/%s" % subreddit.name)
        get_posts_by_subreddit(subreddit)


def get_posts_by_subreddit(subreddit, mark_read=False):
    for submission in reddit.subreddit(subreddit.name).hot(limit=10):
        subreddit, created = Subreddit.objects.get_or_create(id=submission.subreddit.id)
        subreddit.save()
        submissionObj, created = RedditSubmission.objects.get_or_create(id=submission.id, subreddit=subreddit)
        if created:
            logger.info("Found new submission: (%s) %s" % (submissionObj.id, submission.title))
            if mark_read:
                submissionObj.read = True
            submissionObj.subreddit = subreddit
            submissionObj.created_at = datetime.datetime.utcfromtimestamp(submission.created_utc).replace(
                tzinfo=pytz.utc)
            submissionObj.user = submission.author.name
            submissionObj.score = submission.score
            submissionObj.comments = len(submission.comments)
            submissionObj.title = submission.title
            submissionObj.thumbnail = submission.thumbnail

            if submission.is_self:
                submissionObj.selftext = True
                submissionObj.text = submission.selftext
            else:
                logger.info("Submission is a link - trying to get additional info...")
                submissionObj.link = submission.url
                try:
                    g = Goose()
                    article = g.extract(url=submissionObj.link)
                    if article.meta_description is not None and article.meta_description is not "":
                        text = article.meta_description
                    elif article.cleaned_text is not None:
                        text = (article.cleaned_text[:300] + '...') if len(article.cleaned_text) > 300 else article.cleaned_text
                    else:
                        text = None
                    logger.info("Description: %s" % text)
                    submissionObj.text = text
                except Exception as e:
                    logger.error(e)
            submissionObj.permalink = submission.permalink
            submissionObj.save()


class Reddit:
    bot = None

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='addSubreddit', pass_context=True)
    async def add_reddit(self, context, subreddit):
        """Add notifications for new subreddit posts.

        Usage: ?addSubreddit "<subreddit>"

        Examples: ?addSubreddit spacex

        """
        subreddit = subreddit.lower()
        if ' ' in subreddit:
            await self.bot.send_message(context.message.channel, "No spaces in Twitter usernames!")
            return
        try:
            owner_id = context.message.server.owner_id
            author_id = context.message.author.id
        except:
            await self.bot.send_message(context.message.channel, "Only able to run from a server channel.")
            return
        if owner_id == author_id:
            channel, created = SubredditNotificationChannel.objects.get_or_create(name=context.message.channel.name,
                                                                                  channel_id=context.message.channel.id,
                                                                                  server_id=context.message.server.id)
            channel.save()
            await self.add_subreddit(subreddit_name=subreddit, discord_channel=channel)
        else:
            await self.bot.send_message(context.message.channel,
                                        "Only server owners can add Twitter notification channels.")

    @commands.command(name='removeSubreddit', pass_context=True)
    async def remove_reddit(self, context, subreddit):
        """Remove notifications for new subreddit posts.

        Usage: ?removeSubreddit "<subreddit>"

        Examples: ?removeSubreddit spacex

        """
        subreddit = subreddit.lower()
        if ' ' in subreddit:
            await self.bot.send_message(context.message.channel, "No spaces in Subreddit names!")
            return
        try:
            owner_id = context.message.server.owner_id
            author_id = context.message.author.id
        except:
            await self.bot.send_message(context.message.channel, "Only able to run from a server channel.")
            return
        if owner_id == author_id:
            channel, created = SubredditNotificationChannel.objects.get_or_create(name=context.message.channel.name,
                                                                                  channel_id=context.message.channel.id,
                                                                                  server_id=context.message.server.id)
            channel.save()
            await self.remove_subreddit(subreddit_name=subreddit, discord_channel=channel)
        else:
            await self.bot.send_message(context.message.channel,
                                        "Only server owners can add Twitter notification channels.")

    @commands.command(name='listSubreddits', pass_context=True)
    async def list_username(self, context):
        """List subscribed Sub-reddits.

        Usage: ?listSubreddits

        """
        try:
            owner_id = context.message.server.owner_id
            author_id = context.message.author.id
        except:
            await self.bot.send_message(context.message.channel, "Only able to run from a server channel.")
            return
        if owner_id == author_id:
            channel, created = SubredditNotificationChannel.objects.get_or_create(name=context.message.channel.name,
                                                                                  channel_id=context.message.channel.id,
                                                                                  server_id=context.message.server.id)
            channel.save()
            await self.list_subreddit(discord_channel=channel)

    async def reddit_events(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed:
            try:
                await asyncio.wait_for(self.check_submissions(), 30)
            except Exception as e:
                logger.error(e)
            await asyncio.sleep(60)

    async def list_subreddit(self, discord_channel):
        try:
            subreddits = Subreddit.objects.filter(subscribers__channel_id=discord_channel.channel_id)
        except Subreddit.DoesNotExist:
            subreddits = None
        if subreddits is None or len(subreddits) == 0:
            await self.bot.send_message(self.bot.get_channel(id=discord_channel.channel_id),
                                        "Not subscribed to any subreddits in this channel.")
        else:
            description = 'Subreddit Subscriptions: \n\n'
            for subreddit in subreddits:
                description += '/r/%s\n' % subreddit.name
            await self.bot.send_message(self.bot.get_channel(id=discord_channel.channel_id), description)

    async def check_submissions(self):
        logger.debug("Checking for submissions.")
        submissions = RedditSubmission.objects.filter(read=False)
        logger.debug("Found %s submissions to read." % len(submissions))
        for submission in submissions:
            submission.read = True
            submission.save()
            if submission.subreddit.subscribers is not None:
                for channel in submission.subreddit.subscribers.all():
                    logger.debug("Sending %s to %s - %s" % (submission.id, channel.id, channel.name))
                    try:
                        embed = submission_to_embed(submission)
                        await self.bot.send_message(self.bot.get_channel(id=channel.channel_id), embed=embed)
                    except Exception as e:
                        if 'Missing Permissions' in e:
                            channel.delete()
                        logger.error(channel.id)
                        logger.error(channel.name)
                        logger.error(e)

    async def add_subreddit(self, subreddit_name, discord_channel):
        try:
            for submission in reddit.subreddit(subreddit_name).hot(limit=1):
                subreddit, created = Subreddit.objects.get_or_create(id=submission.subreddit.id)
                subreddit.name = submission.subreddit.display_name
                if subreddit.subscribers is not None and len(
                        subreddit.subscribers.all().filter(channel_id=discord_channel.channel_id)) > 0:
                    await self.bot.send_message(self.bot.get_channel(id=discord_channel.channel_id),
                                                'Already subscribed to /r/%s in this channel.' % subreddit_name)
                    return
                else:
                    subreddit.subscribers.add(discord_channel)
                    subreddit.save()
                    if not subreddit.initialized:
                        await self.bot.send_message(self.bot.get_channel(id=discord_channel.channel_id),
                                                    "Checking...one sec!")
                        get_posts_by_subreddit(subreddit, mark_read=True)
                        subreddit.initialized = True
                    subreddit.save()
                    await self.bot.send_message(self.bot.get_channel(id=discord_channel.channel_id),
                                                "Subscribed to /r/%s in this channel.\n\n"
                                                "Here's the latest Hot post:\n" % subreddit_name,
                                                embed=submission_to_embed(
                                                    subreddit.submissions.order_by('created_at').first()))
        except Redirect as e:
            await self.bot.send_message(self.bot.get_channel(id=discord_channel.channel_id), "Subreddit doesn't exist.")

    async def remove_subreddit(self, subreddit_name, discord_channel):
        try:
            subreddit = Subreddit.objects.get(name=subreddit_name)
        except Subreddit.DoesNotExist:
            subreddit = None
        if subreddit is None:
            await self.bot.send_message(self.bot.get_channel(id=discord_channel.channel_id),
                                        "Not subscribed to /r/%s in this channel." % subreddit_name)
        else:
            if len(Subreddit.objects.filter(subscribers__in=[discord_channel])) > 0:
                subreddit.subscribers.remove(discord_channel)
                if len(subreddit.subscribers.all()) == 0:
                    subreddit.delete()
                else:
                    subreddit.save()
                await self.bot.send_message(self.bot.get_channel(id=discord_channel.channel_id),
                                            "Unsubscribed from /r/%s in this channel." % subreddit_name)
            else:
                await self.bot.send_message(self.bot.get_channel(id=discord_channel.channel_id),
                                            "Not subscribed to /r/%s in this channel." % subreddit_name)


def setup(bot):
    reddit_bot = Reddit(bot)
    bot.add_cog(reddit_bot)
    bot.loop.create_task(reddit_bot.reddit_events())
