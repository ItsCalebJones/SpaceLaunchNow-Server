from api.v330.common.serializers import *


class SpacecraftFlightSerializerForDockingEvent(serializers.HyperlinkedModelSerializer):
    spacecraft = serializers.StringRelatedField(read_only=True, many=False)

    class Meta:
        model = SpacecraftFlight
        fields = ('id', 'url', 'destination', 'splashdown', 'spacecraft')


class DockingEventSerializer(serializers.HyperlinkedModelSerializer):
    flight_vehicle = SpacecraftFlightSerializerForDockingEvent(read_only=True)
    docking_location = serializers.StringRelatedField(many=False, read_only=True)

    class Meta:
        model = DockingEvent
        fields = ('id', 'url', 'docking', 'departure', 'flight_vehicle', 'docking_location')


class DockingEventDetailedSerializer(serializers.HyperlinkedModelSerializer):
    flight_vehicle = SpacecraftFlightSerializerForDockingEvent(read_only=True, many=False)
    docking_location = serializers.StringRelatedField(many=False, read_only=True)

    class Meta:
        model = DockingEvent
        fields = ('id', 'url', 'docking', 'departure', 'flight_vehicle', 'docking_location')
