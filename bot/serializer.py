from bot.models import Launch, Location, Rocket, Mission, Notification
from rest_framework import serializers


class NotificationSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Notification
        fields = (
            'launch', 'url', 'wasNotifiedTwentyFourHour', 'wasNotifiedOneHour', 'wasNotifiedTenMinutes', 'wasNotifiedDailyDigest',
            'last_daily_digest_post', 'last_twitter_post'
        )
        extra_kwargs = {
            'id': {'read_only': False},
            'slug': {'validators': []},
        }


class RocketSerializer(serializers.HyperlinkedModelSerializer):
    rocket_id = serializers.IntegerField()

    class Meta:
        model = Rocket
        fields = (
            'rocket_id', 'name', 'configuration', 'familyName'

        )
        extra_kwargs = {
            'rocket_id': {'read_only': False},
            'slug': {'validators': []},
        }


class MissionSerializer(serializers.HyperlinkedModelSerializer):
    mission_id = serializers.IntegerField()

    class Meta:
        model = Mission
        fields = (
            'mission_id', 'name', 'description', 'type', 'typeName'
        )
        extra_kwargs = {
            'mission_id': {'read_only': False},
            'slug': {'validators': []},
        }


class LocationSerializer(serializers.HyperlinkedModelSerializer):
    location_id = serializers.IntegerField()

    class Meta:
        model = Location
        fields = (
            'location_id', 'name', 'infoURL', 'wikiURL'
        )
        extra_kwargs = {
            'location_id': {'read_only': False},
            'slug': {'validators': []},
        }


class LaunchSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField()
    location = LocationSerializer()
    rocket = RocketSerializer()
    missions = MissionSerializer(many=True)

    class Meta:
        model = Launch
        fields = (
            'id', 'name', 'url', 'status', 'netstamp', 'wsstamp', 'westamp', 'location', 'rocket', 'missions'
        )
        extra_kwargs = {
            'id': {'read_only': False},
            'slug': {'validators': []},
        }

    def create(self, validated_data):
        location_data = validated_data.pop('location')
        location = Location.objects.get_or_create(**location_data)[0]
        rocket_data = validated_data.pop('rocket')
        rocket = Rocket.objects.get_or_create(**rocket_data)[0]
        mission_data = validated_data.pop('missions')
        launch = Launch.objects.get_or_create(location=location, rocket=rocket,
                                              **validated_data)
        Notification.objects.get_or_create(launch=launch[0])
        for mission in mission_data:
            Mission.objects.get_or_create(launch=launch[0], **mission)
        return launch

    def update(self, instance, validated_data):
        instance.id = validated_data.get('id', instance.id)
        instance.name = validated_data.get('name', instance.name)
        instance.status = validated_data.get('status', instance.status)
        instance.netstamp = validated_data.get('netstamp', instance.netstamp)
        instance.wsstamp = validated_data.get('wsstamp', instance.wsstamp)
        instance.westamp = validated_data.get('westamp', instance.westamp)
        instance.save()

        location = validated_data.get('location')
        location_id = location.get('id', None)
        if location_id:
            location_item = Location.objects.get(location_id=location_id, launch=instance)
            location_item.id = location.get('id', location_item.id)
            location_item.name = location.get('name', location_item.name)
            location_item.infoURL = location.get('infoURL', location_item.infoURL)
            location_item.wikiURL = location.get('wikiURL', location_item.wikiURL)
            location_item.save()
        else:
            Location.objects.create(location)

        rocket = validated_data.get('rocket')
        rocket_id = rocket.get('id', None)
        if rocket_id:
            rocket_item = Rocket.objects.get(id=rocket_id, launch=instance)
            rocket_item.id = rocket.get('id', rocket_item.id)
            rocket_item.name = rocket.get('name', rocket_item.name)
            rocket_item.configuration = rocket.get('configuration', rocket_item.configuration)
            rocket_item.familyName = rocket.get('familyName', rocket_item.familyName)
            rocket_item.wikiURL = rocket.get('wikiURL', rocket_item.wikiURL)
            rocket_item.save()
        else:
            Rocket.objects.create(rocket)

        missions = validated_data.get('missions')
        if missions:
            for mission in missions:
                mission_id = mission.get('id', None)
                if mission_id:
                    mission_item = Mission.objects.get(id=mission_id, launch=instance)
                    mission_item.name = mission.get('name', mission_item.name)
                    mission_item.description = mission.get('description', mission_item.description)
                    mission_item.type = mission.get('type', mission_item.type)
                    mission_item.typeName = mission.get('typeName', mission_item.typeName)
                    mission_item.save()
                else:
                    Mission.objects.create(launch=instance, **item)
        return instance

    def get_object(self):
        return self.model(self.validated_data)
