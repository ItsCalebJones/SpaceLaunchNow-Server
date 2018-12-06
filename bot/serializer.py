from bot.models import Launch, Notification, DailyDigestRecord
from rest_framework import serializers


class NotificationSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Notification
        fields = (
            'launch', 'url', 'wasNotifiedTwentyFourHour', 'wasNotifiedOneHour', 'wasNotifiedTenMinutes',
            'wasNotifiedDailyDigest', 'last_twitter_post', 'last_net_stamp',
            'last_net_stamp_timestamp'
        )
        extra_kwargs = {
            'id': {'read_only': False},
            'slug': {'validators': []},
        }


class DailyDigestRecordSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = DailyDigestRecord
        fields = '__all__'

