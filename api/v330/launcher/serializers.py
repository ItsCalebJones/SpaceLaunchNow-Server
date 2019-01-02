from api.v330.common.serializers import *


class LauncherSerializer(QueryFieldsMixin, serializers.ModelSerializer):
    launcher_config = LauncherConfigListSerializer(read_only=True)

    class Meta:
        model = Launcher
        fields = ('id', 'url', 'flight_proven', 'serial_number', 'status', 'previous_flights', 'details', 'launcher_config')


class LauncherDetailSerializer(QueryFieldsMixin, serializers.ModelSerializer):
    launcher_config = LauncherConfigDetailSerializer(read_only=True)

    class Meta:
        model = Launcher
        fields = ('id', 'url', 'flight_proven', 'serial_number', 'status', 'previous_flights', 'details',
                  'launcher_config')
