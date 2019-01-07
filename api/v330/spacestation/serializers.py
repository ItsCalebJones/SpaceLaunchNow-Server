from api.v330.common.serializers import *


class DockingEventDetailedSerializerForSpacestation(serializers.HyperlinkedModelSerializer):
    flight_vehicle = serializers.StringRelatedField(read_only=True, many=False)
    docking_location = serializers.StringRelatedField(many=False, read_only=True)

    class Meta:
        model = DockingEvent
        fields = ('id', 'url', 'docking', 'departure', 'flight_vehicle', 'docking_location')


class AstronautFlightForExpeditionSerializer(serializers.ModelSerializer):
    role = serializers.StringRelatedField(read_only=True, source='role.role')
    astronaut = AstronautSerializer(read_only=True, many=False)

    class Meta:
        model = AstronautFlight
        fields = ('role', 'astronaut')


class ExpeditionSerializerForSpacestation(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Expedition
        fields = ('id', 'url', 'name', 'start', 'end',)


class ExpeditionDetailedSerializerForSpacestation(serializers.HyperlinkedModelSerializer):
    crew = AstronautFlightForExpeditionSerializer(many=True, read_only=True)

    class Meta:
        model = Expedition
        fields = ('id', 'url', 'name', 'start', 'end', 'crew')


class SpaceStationDetailedSerializer(serializers.HyperlinkedModelSerializer):
    status = SpaceStationStatusSerializer(read_only=True, many=False)
    owners = AgencySerializer(read_only=True, many=True)
    orbit = serializers.StringRelatedField(many=False, read_only=True)
    docked_vehicles = SpacecraftFlightSerializer(read_only=True, many=True)
    active_expeditions = ExpeditionDetailedSerializerForSpacestation(read_only=True, many=True)

    class Meta:
        model = SpaceStation
        fields = ('id', 'url', 'name', 'status', 'founded', 'description', 'orbit', 'onboard_crew', 'owners', 'docked_vehicles',
                  'active_expeditions',)


class SpaceStationSerializer(serializers.HyperlinkedModelSerializer):
    status = SpaceStationStatusSerializer(read_only=True, many=False)
    owners = AgencyListSerializer(read_only=True, many=True)
    orbit = serializers.StringRelatedField(many=False, read_only=True)
    active_expedition = ExpeditionSerializerForSpacestation(read_only=True, many=True)

    class Meta:
        model = SpaceStation
        fields = ('id', 'url', 'name', 'status', 'founded', 'description', 'orbit',  'owners', 'active_expedition',)
