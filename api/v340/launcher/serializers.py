from api.v340.common.serializers import *


class LauncherSerializer(QueryFieldsMixin, serializers.ModelSerializer):
    launcher_config = LauncherConfigListSerializer(read_only=True)

    class Meta:
        model = Launcher
        fields = ('id', 'url', 'flight_proven', 'serial_number', 'status', 'details',
                  'launcher_config', 'image_url', 'flights')


class LauncherDetailSerializer(QueryFieldsMixin, serializers.ModelSerializer):
    launcher_config = LauncherConfigDetailSerializer(read_only=True)

    class Meta:
        model = Launcher
        fields = ('id', 'url', 'flight_proven', 'serial_number', 'status', 'previous_flights', 'details',
                  'launcher_config', 'image_url', 'successful_landings', 'attempted_landings', 'flights')
