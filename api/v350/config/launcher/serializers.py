from api.v350.common.serializers import *


class LauncherConfigSerializerForLauncher(QueryFieldsMixin, serializers.ModelSerializer):

    class Meta:
        model = LauncherConfig
        fields = ('id', 'launch_library_id', 'url', 'name', 'family', 'full_name', 'variant', 'image_url', 'info_url',
                  'wiki_url', 'total_launch_count', 'consecutive_successful_launches', 'successful_launches',
                  'failed_launches', 'pending_launches',)
