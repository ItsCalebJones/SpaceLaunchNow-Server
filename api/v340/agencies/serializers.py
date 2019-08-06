from api.v340.common.serializers import *


class LauncherConfigDetailSerializerForAgency(QueryFieldsMixin, serializers.ModelSerializer):

    def get_rep(self, obj):
        rep = obj.rep
        serializer_context = {'request': self.context.get('request'),
                              'id': obj.id}
        serializer = AgencySerializer(rep, context=serializer_context)
        return serializer.data

    class Meta:
        model = LauncherConfig
        fields = ('id', 'launch_library_id', 'url', 'name', 'description', 'family', 'full_name',
                  'variant', 'alias', 'min_stage', 'max_stage', 'length', 'diameter',
                  'maiden_flight', 'launch_mass', 'leo_capacity', 'gto_capacity',
                  'to_thrust', 'apogee', 'vehicle_range', 'image_url', 'info_url', 'wiki_url',
                  'consecutive_successful_launches', 'successful_launches', 'failed_launches', 'pending_launches',)


class AgencySerializerDetailed(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    parent = serializers.StringRelatedField(read_only=True)
    launcher_list = LauncherConfigDetailSerializerForAgency(many=True, read_only=True)
    spacecraft_list = SpacecraftConfigurationDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Agency
        fields = ('id', 'url', 'name', 'featured', 'type', 'country_code', 'abbrev', 'description', 'administrator',
                  'founding_year', 'launchers', 'spacecraft', 'parent', 'launch_library_url', 'total_launch_count',
                  'successful_launches', 'consecutive_successful_launches', 'failed_launches', 'pending_launches',
                  'successful_landings', 'failed_landings', 'attempted_landings', 'info_url', 'wiki_url',  'logo_url',
                  'image_url', 'nation_url', 'launcher_list', 'spacecraft_list',)

    def get_fields(self):
        fields = super(AgencySerializerDetailed, self).get_fields()
        return fields
