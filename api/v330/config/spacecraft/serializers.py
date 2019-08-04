from api.v330.common.serializers import *


class SpacecraftConfigurationDetailSerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    agency = AgencySerializer(read_only=True, many=False, source='manufacturer')

    class Meta:
        model = SpacecraftConfiguration
        fields = ('id', 'url', 'name', 'agency', 'in_use', 'capability', 'history', 'details', 'maiden_flight',
                  'height', 'diameter', 'human_rated', 'crew_capacity', 'payload_capacity', 'flight_life',
                  'image_url', 'nation_url', 'wiki_link', 'info_link')


class SpacecraftConfigurationSerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    agency = AgencySerializerMini(read_only=True, many=False, source='manufacturer')

    class Meta:
        model = SpacecraftConfiguration
        fields = ('id', 'url', 'name', 'agency', 'in_use', 'capability', 'maiden_flight',
                  'human_rated', 'crew_capacity', 'image_url', 'nation_url', 'wiki_link', 'info_link')
