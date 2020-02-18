from api.v350.common.serializers import *


class SpaceStationDetailedSerializerForExpedition(serializers.HyperlinkedModelSerializer):
    status = SpaceStationStatusSerializer(read_only=True, many=False)
    owners = AgencyListSerializer(read_only=True, many=True)
    orbit = serializers.StringRelatedField(many=False, read_only=True)

    class Meta:
        model = SpaceStation
        fields = ('id', 'url', 'name', 'status', 'founded', 'description', 'orbit', 'image_url', 'owners',)


class ExpeditionDetailSerializer(serializers.HyperlinkedModelSerializer):
    crew = AstronautFlightForExpeditionSerializer(many=True, read_only=True)
    spacestation = SpaceStationDetailedSerializerForExpedition(many=False, read_only=True, source='space_station')

    class Meta:
        model = Expedition
        fields = ('id', 'url', 'name', 'start', 'end', 'spacestation', 'crew')

