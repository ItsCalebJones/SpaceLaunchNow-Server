from api.v330.common.serializers import *


class DockingEventDetailedSerializerForSpacestation(serializers.HyperlinkedModelSerializer):
    flight_vehicle = serializers.StringRelatedField(read_only=True, many=False)
    docking_location = serializers.StringRelatedField(many=False, read_only=True)

    class Meta:
        model = DockingEvent
        fields = ('id', 'url', 'docking', 'departure', 'flight_vehicle', 'docking_location')


class ExpeditionSerializerForSpacestation(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Expedition
        fields = ('id', 'url', 'name', 'start', 'end',)


class SpaceStationDetailedSerializer(serializers.HyperlinkedModelSerializer):
    status = SpaceStationStatusSerializer(read_only=True, many=False)
    owners = AgencySerializer(read_only=True, many=True)
    orbit = serializers.StringRelatedField(many=False, read_only=True)
    docking_events = DockingEventDetailedSerializerForSpacestation(read_only=True, many=True)
    expedition = ExpeditionSerializerForSpacestation(read_only=True, many=True)

    class Meta:
        model = SpaceStation
        fields = ('id', 'url', 'name', 'status', 'founded', 'description', 'orbit', 'owners', 'docking_events', 'expedition')


class SpaceStationSerializer(serializers.HyperlinkedModelSerializer):
    status = SpaceStationStatusSerializer(read_only=True, many=False)
    owners = AgencyListSerializer(read_only=True, many=True)
    orbit = serializers.StringRelatedField(many=False, read_only=True)

    class Meta:
        model = SpaceStation
        fields = ('id', 'url', 'name', 'status', 'founded', 'description', 'orbit',  'owners',)