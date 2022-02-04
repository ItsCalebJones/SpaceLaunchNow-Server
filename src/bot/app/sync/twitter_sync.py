import datetime
import logging
import time

import pytz
from twitter import Twitter, OAuth, TwitterError

from bot.models import Tweet, TwitterUser, TwitterNotificationChannel
from spacelaunchnow import config

twitter = Twitter(auth=OAuth(consumer_key=config.keys['CONSUMER_KEY'],
                             consumer_secret=config.keys['CONSUMER_SECRET'],
                             token=config.keys['TOKEN_KEY'],
                             token_secret=config.keys['TOKEN_SECRET']))

logger = logging.getLogger('bot.discord.tweets')


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
