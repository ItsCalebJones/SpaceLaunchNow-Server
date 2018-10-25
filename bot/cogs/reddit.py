import asyncio

from discord.ext import commands

from bot.models import SubredditNotificationChannel, Subreddit, RedditSubmission

import praw

from bot.utils import config

user_agent = 'Space Launch News Bot'
reddit = praw.Reddit(client_id=config.REDDIT_CLIENT_ID,
                     client_secret=config.REDDIT_CLIENT_SECRET,
                     user_agent=config.REDDIT_AGENT,)

reddit.read_only = True


class Reddit:
    bot = None

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='addReddit', pass_context=True)
    async def add_reddit(self, context, subreddit):
        """Add a custom Twitter account for notifications.

        Usage: ?addTwitterUsername "<username>"

        Examples: ?addTwitterUsername "elonmusk"

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

    @commands.command(name='removeReddit', pass_context=True)
    async def remove_reddit(self, ctx, reddit_user):
        return

    async def reddit_events(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed:
            await self.get_submissions()
            await self.check_submissions()
            await asyncio.sleep(5)

    async def get_submissions(self):
        print("Getting submissions.")
        subreddits = Subreddit.objects.all()

        for subreddit in subreddits:
            for submission in reddit.subreddit(subreddit.name).hot(limit=10):
                subreddit, created = Subreddit.objects.get_or_create(id=submission.subreddit.id)
                subreddit.save()
                submissionObj, created = RedditSubmission.objects.get_or_create(id=submission.id, subreddit=subreddit)
                if created:
                    submissionObj.subreddit = subreddit
                    submissionObj.user = submission.author.name
                    if submission.is_self:
                        submissionObj.text = submission.selftext
                    else:
                        submissionObj.link = submission.url
                    submissionObj.permalink = submission.permalink
                    submissionObj.save()

    async def check_submissions(self):
        print("Checking submissions.")
        submissions = RedditSubmission.objects.filter(read=False)
        for submission in submissions:
            submission.read = True
            submission.save()
            if submission.subreddit.subscribers is not None:
                for channel in submission.subreddit.subscribers.all():
                    await self.bot.send_message(self.bot.get_channel(id=channel.channel_id), "Hello")
                                                # embed=submission_to_embed(submission))

    async def add_subreddit(self, subreddit_name, discord_channel):
        for submission in reddit.subreddit(subreddit_name).hot(limit=1):
            subreddit, created = Subreddit.objects.get_or_create(id=submission.subreddit.id)
            subreddit.name = submission.subreddit.display_name
            subreddit.subscribers.add(discord_channel)
            subreddit.save()


def setup(bot):
    reddit_bot = Reddit(bot)
    bot.add_cog(reddit_bot)
    bot.loop.create_task(reddit_bot.reddit_events())
