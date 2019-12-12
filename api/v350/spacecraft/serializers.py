from api.v350.common.serializers import *


class SpacecraftDetailedSerializer(serializers.HyperlinkedModelSerializer):
    status = SpacecraftStatusSerializer(read_only=True, many=False)
    spacecraft_config = SpacecraftConfigurationDetailSerializer(read_only=True, many=False)
    flights = SpacecraftFlightSerializer(read_only=True, many=True, source='spacecraftflight')

    class Meta:
        model = Spacecraft
        fields = ('id', 'url', 'name', 'serial_number', 'status', 'description', 'spacecraft_config', 'flights')


class SpacecraftSerializer(serializers.HyperlinkedModelSerializer):
    status = SpacecraftStatusSerializer(read_only=True, many=False)
    configuration = SpacecraftConfigSerializer(read_only=True, many=False, source='spacecraft_config')

    class Meta:
        model = Spacecraft
        fields = ('id', 'url', 'name', 'serial_number', 'status', 'description', 'configuration')