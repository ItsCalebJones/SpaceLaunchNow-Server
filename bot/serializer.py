from bot.models import Launch, Location, Rocket, Mission
from rest_framework import serializers


class RocketSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = Rocket
        fields = (
            'id', 'name'
        )


class MissionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = Mission
        fields = (
            'id', 'name'
        )


class LocationSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = Location
        fields = (
            'id', 'name'
        )

    def create(self, validated_data):
        return Location.objects.get_or_create(**validated_data)

    def update(self, instance, validated_data):
        instance.id = validated_data.get('id', instance.id)
        instance.name = validated_data.get('name', instance.name)
        return instance


class LaunchSerializer(serializers.ModelSerializer):
    location = LocationSerializer()
    rocket = RocketSerializer()
    missions = MissionSerializer(many=True)

    class Meta:
        model = Launch
        fields = (
            'id', 'name', 'status', 'netstamp', 'wsstamp', 'westamp', 'location', 'rocket', 'missions'
        )

    def create(self, validated_data):
        location_data = validated_data.pop('location')
        location = Location.objects.get_or_create(**location_data)[0]
        rocket_data = validated_data.pop('rocket')
        rocket = Rocket.objects.get_or_create(**rocket_data)[0]
        mission_data = validated_data.pop('missions')
        launch = Launch.objects.get_or_create(location=location, rocket=rocket, **validated_data)
        for mission in mission_data:
            Mission.objects.get_or_create(launch=launch[0], **mission)
        return launch

    def update(self, instance, validated_data):
        instance.id = validated_data.get('id', instance.id)
        instance.name = validated_data.get('name', instance.name)
        return instance

    def get_object(self):
        return self.model(self.validated_data)
