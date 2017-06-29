from bot.models import Launch, Notification
from rest_framework import serializers


class NotificationSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Notification
        fields = (
            'launch', 'url', 'wasNotifiedTwentyFourHour', 'wasNotifiedOneHour', 'wasNotifiedTenMinutes',
            'wasNotifiedDailyDigest', 'last_daily_digest_analysis', 'last_twitter_post', 'last_net_stamp',
            'last_net_stamp_timestamp'
        )
        extra_kwargs = {
            'id': {'read_only': False},
            'slug': {'validators': []},
        }


class LaunchSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Launch
        fields = (
            'id', 'name', 'url', 'status',
            'netstamp', 'wsstamp', 'westamp',
            'location_name', 'rocket_name', 'mission_name'
        )

    def create(self, validated_data):
        launch = Launch.objects.get_or_create(**validated_data)
        try:
            if Notification.objects.get(launch=launch[0]) is None:
                Notification.objects.get_or_create(launch=launch[0])
        except:
            Notification.objects.get_or_create(launch=launch[0])
        return launch

    def update(self, instance, validated_data):
        instance.id = validated_data.get('id', instance.id)
        instance.name = validated_data.get('name', instance.name)
        instance.status = validated_data.get('status', instance.status)
        instance.netstamp = validated_data.get('netstamp', instance.netstamp)
        instance.wsstamp = validated_data.get('wsstamp', instance.wsstamp)
        instance.westamp = validated_data.get('westamp', instance.westamp)
        instance.location_name = validated_data.get('location_name', instance.location_name)
        instance.rocket_name = validated_data.get('rocket_name', instance.rocket_name)
        instance.mission_name = validated_data.get('mission_name', instance.mission_name)
        instance.save()

        return instance

    def get_object(self):
        return self.model(self.validated_data)

