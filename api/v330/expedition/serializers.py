from api.v330.common.serializers import *


class AstronautFlightForExpeditionSerializer(serializers.ModelSerializer):
    role = serializers.StringRelatedField(read_only=True, source='role.role')
    astronaut = AstronautSerializer(read_only=True, many=False)

    class Meta:
        model = AstronautFlight
        fields = ('role', 'astronaut')


class SpaceStationDetailedSerializerForExpedition(serializers.HyperlinkedModelSerializer):
    status = SpaceStationStatusSerializer(read_only=True, many=False)
    owners = AgencyListSerializer(read_only=True, many=True)
    orbit = serializers.StringRelatedField(many=False, read_only=True)

    class Meta:
        model = SpaceStation
        fields = ('id', 'url', 'name', 'status', 'founded', 'description', 'orbit', 'owners',)


class SpaceStationSerializerForExpedition(serializers.HyperlinkedModelSerializer):
    status = SpaceStationStatusSerializer(read_only=True, many=False)
    orbit = serializers.StringRelatedField(many=False, read_only=True)

    class Meta:
        model = SpaceStation
        fields = ('id', 'url', 'name', 'status', 'orbit')


class ExpeditionDetailSerializer(serializers.HyperlinkedModelSerializer):
    crew = AstronautFlightForExpeditionSerializer(many=True, read_only=True)
    spacestation = SpaceStationDetailedSerializerForExpedition(many=False, read_only=True, source='space_station')

    class Meta:
        model = Expedition
        fields = ('id', 'url', 'name', 'start', 'end', 'spacestation', 'crew')


class ExpeditionSerializer(serializers.HyperlinkedModelSerializer):
    spacestation = SpaceStationSerializerForExpedition(many=False, read_only=True, source='space_station')

    class Meta:
        model = Expedition
        fields = ('id', 'url', 'name', 'start', 'end', 'spacestation')
