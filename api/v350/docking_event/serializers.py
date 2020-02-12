from api.v350.common.serializers import *


class SpacecraftDetailedNoFlightsSerializer(serializers.HyperlinkedModelSerializer):
    status = SpacecraftStatusSerializer(read_only=True, many=False)
    configuration = SpacecraftConfigurationDetailSerializer(read_only=True, many=False)

    class Meta:
        model = Spacecraft
        fields = ('id', 'url', 'name', 'serial_number', 'status', 'description', 'configuration',)


class SpacecraftFlightSerializerForDockingEvent(serializers.HyperlinkedModelSerializer):
    spacecraft = SpacecraftSerializer(read_only=True, many=False)

    class Meta:
        model = SpacecraftFlight
        fields = ('id', 'url', 'destination', 'mission_end', 'spacecraft')


class SpacecraftFlightDetailedSerializerForDockingEvent(serializers.HyperlinkedModelSerializer):
    spacecraft = SpacecraftDetailedNoFlightsSerializer(read_only=True, many=False)

    class Meta:
        model = SpacecraftFlight
        fields = ('id', 'url', 'destination', 'mission_end', 'spacecraft')


class SpaceStationSerializerForDockingEvent(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SpaceStation
        fields = ('id', 'url', 'name', 'image_url')


class DockingEventSerializer(serializers.HyperlinkedModelSerializer):
    launch_id = serializers.CharField(source='flight_vehicle.rocket.launch.id')
    flight_vehicle = SpacecraftFlightSerializerForDockingEvent(read_only=True)
    docking_location = DockingLocationSerializer(many=False, read_only=True)

    class Meta:
        model = DockingEvent
        fields = ('id', 'url', 'launch_id', 'docking', 'departure', 'flight_vehicle', 'docking_location')


class DockingEventDetailedSerializer(serializers.HyperlinkedModelSerializer):
    launch_id = serializers.CharField(source='flight_vehicle.rocket.launch.id')
    flight_vehicle = SpacecraftFlightDetailedSerializerForDockingEvent(read_only=True)
    docking_location = DockingLocationSerializer(many=False, read_only=True)
    space_station = SpaceStationSerializerForDockingEvent(many=False, read_only=True)

    class Meta:
        model = DockingEvent
        fields = ('id', 'url', 'launch_id', 'docking', 'departure', 'flight_vehicle', 'docking_location', 'space_station')
