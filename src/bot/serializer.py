from rest_framework import serializers

from bot.models import DailyDigestRecord, LaunchNotificationRecord


class NotificationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LaunchNotificationRecord
        fields = (
            "launch_id",
            "url",
            "wasNotifiedTwentyFourHour",
            "wasNotifiedOneHour",
            "wasNotifiedTenMinutes",
            "wasNotifiedDailyDigest",
            "last_twitter_post",
            "last_net_stamp",
            "last_net_stamp_timestamp",
        )
        extra_kwargs = {
            "id": {"read_only": False},
            "slug": {"validators": []},
        }


class DailyDigestRecordSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DailyDigestRecord
        fields = "__all__"
