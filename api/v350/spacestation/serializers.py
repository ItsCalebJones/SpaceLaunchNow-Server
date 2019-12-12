from api.v350.common.serializers import *


class SpacecraftFlightForDockingEvent(serializers.HyperlinkedModelSerializer):
    spacecraft = SpacecraftDetailedNoFlightsSerializer(read_only=True, many=False)
    launch = LaunchListSerializer(read_only=True, many=False, source='rocket.launch')
    id = serializers.IntegerField(source='pk')

    class Meta:
        model = SpacecraftFlight
        fields = (
            'id', 'url', 'spacecraft', 'launch', )


class DockingEventDetailedSerializerForSpacestation(serializers.HyperlinkedModelSerializer):
    flight_vehicle = SpacecraftFlightForDockingEvent(read_only=True, many=False)

    class Meta:
        model = DockingEvent
        fields = ('id', 'url', 'docking', 'departure', 'flight_vehicle',)


class ExpeditionSerializerForSpacestation(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Expedition
        fields = ('id', 'url', 'name', 'start', 'end',)


class ExpeditionDetailedSerializerForSpacestation(serializers.HyperlinkedModelSerializer):
    crew = AstronautFlightForExpeditionSerializer(many=True, read_only=True)

    class Meta:
        model = Expedition
        fields = ('id', 'url', 'name', 'start', 'end', 'crew')


class DockingLocationSerializerForSpacestation(serializers.ModelSerializer):
    docked = DockingEventDetailedSerializerForSpacestation(read_only=True, many=False)

    class Meta:
        model = DockingLocation
        fields = ('id', 'name', 'docked',)


class SpaceStationDetailedSerializer(serializers.HyperlinkedModelSerializer):
    status = SpaceStationStatusSerializer(read_only=True, many=False)
    owners = AgencySerializer(read_only=True, many=True)
    type = SpaceStationTypeSerializer(read_only=True, many=False)
    orbit = serializers.StringRelatedField(many=False, read_only=True)
    active_expeditions = ExpeditionDetailedSerializerForSpacestation(read_only=True, many=True)
    docking_location = DockingLocationSerializerForSpacestation(read_only=True, many=True)

    class Meta:
        model = SpaceStation
        fields = ('id', 'url', 'name', 'status', 'type', 'founded', 'deorbited', 'height', 'width', 'mass', 'volume',
                  'description', 'orbit', 'onboard_crew', 'owners', 'active_expeditions', 'docking_location',
                  'image_url')


class SpaceStationSerializer(serializers.HyperlinkedModelSerializer):
    status = SpaceStationStatusSerializer(read_only=True, many=False)
    type = SpaceStationTypeSerializer(read_only=True, many=False)
    owners = AgencyListSerializer(read_only=True, many=True)
    orbit = serializers.StringRelatedField(many=False, read_only=True)
    active_expedition = ExpeditionSerializerForSpacestation(read_only=True, many=True)

    class Meta:
        model = SpaceStation
        fields = ('id', 'url', 'name', 'status', 'type', 'founded', 'deorbited', 'description', 'orbit',  'owners',
                  'active_expedition', 'image_url',)
