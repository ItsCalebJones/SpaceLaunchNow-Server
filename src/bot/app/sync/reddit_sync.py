import datetime
import logging

import praw
import pytz
from goose3 import Goose
from twitter import OAuth, Twitter

from bot.models import RedditSubmission, Subreddit
from spacelaunchnow import config

user_agent = "Space Launch News Bot"
reddit = praw.Reddit(
    client_id=config.REDDIT_CLIENT_ID,
    client_secret=config.REDDIT_CLIENT_SECRET,
    user_agent=config.REDDIT_AGENT,
)

reddit.read_only = True

twitter = Twitter(
    auth=OAuth(
        consumer_key=config.keys["CONSUMER_KEY"],
        consumer_secret=config.keys["CONSUMER_SECRET"],
        token=config.keys["TOKEN_KEY"],
        token_secret=config.keys["TOKEN_SECRET"],
    )
)

logger = logging.getLogger("bot.discord")


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
        submissionObj, created = RedditSubmission.objects.get_or_create(
            id=submission.id, subreddit=subreddit
        )
        if created:
            logger.info(
                "Found new submission: (%s) %s" % (submissionObj.id, submission.title)
            )
            if mark_read:
                submissionObj.read = True
            submissionObj.subreddit = subreddit
            submissionObj.created_at = datetime.datetime.utcfromtimestamp(
                submission.created_utc
            ).replace(tzinfo=pytz.utc)
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
                    if (
                        article.meta_description is not None
                        and article.meta_description != ""
                    ):
                        text = article.meta_description
                    elif article.cleaned_text is not None:
                        text = (
                            (article.cleaned_text[:300] + "...")
                            if len(article.cleaned_text) > 300
                            else article.cleaned_text
                        )
                    else:
                        text = None
                    logger.info("Description: %s" % text)
                    submissionObj.text = text
                except Exception as e:
                    logger.error(e)
            submissionObj.permalink = submission.permalink
            submissionObj.save()
