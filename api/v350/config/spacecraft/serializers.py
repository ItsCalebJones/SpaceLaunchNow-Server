from api.v350.common.serializers import *


class SpacecraftConfigurationSerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    agency = AgencySerializer(read_only=True, many=False, source='manufacturer')

    class Meta:
        model = SpacecraftConfiguration
        fields = ('id', 'url', 'name', 'agency', 'in_use', 'capability', 'maiden_flight',
                  'human_rated', 'crew_capacity', 'image_url', 'nation_url', 'wiki_link', 'info_link')
