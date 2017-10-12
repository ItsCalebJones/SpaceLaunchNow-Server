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


class LaunchSerializer(serializers.HyperlinkedModelSerializer):
    vid_urls = serializers.StringRelatedField(many=True)

    class Meta:
        model = Launch
        fields = (
            'id', 'name', 'url', 'img_url', 'status', 'netstamp', 'wsstamp', 'westamp', 'location_name', 'rocket_name',
            'mission_name', 'mission_description', 'mission_type', 'net', 'window_start', 'window_end', 'vid_urls'
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
        instance.img_url = validated_data.get('img_url', instance.img_url)
        instance.status = validated_data.get('status', instance.status)
        instance.netstamp = validated_data.get('netstamp', instance.netstamp)
        instance.wsstamp = validated_data.get('wsstamp', instance.wsstamp)
        instance.westamp = validated_data.get('westamp', instance.westamp)
        instance.location_name = validated_data.get('location_name', instance.location_name)
        instance.rocket_name = validated_data.get('rocket_name', instance.rocket_name)
        instance.mission_name = validated_data.get('mission_name', instance.mission_name)
        instance.mission_description = validated_data.get('mission_description', instance.mission_description)
        instance.mission_type = validated_data.get('mission_type', instance.mission_type)
        instance.save()

        return instance

    def get_object(self):
        return self.model(self.validated_data)

