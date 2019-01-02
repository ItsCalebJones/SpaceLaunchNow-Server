from api.v330.common.serializers import *


class AstronautDetailedSerializer(serializers.HyperlinkedModelSerializer):
    status = AstronautStatusSerializer(read_only=True)
    agency = AgencySerializerMini(read_only=True, many=False)
    flights = LaunchListSerializer(read_only=True, many=True)

    class Meta:
        model = Astronauts
        # fields = ('name',)
        fields = ('id', 'url', 'name', 'status', 'agency', 'date_of_birth', 'date_of_death', 'nationality',
                  'twitter', 'instagram', 'bio', 'profile_image', 'wiki', 'flights')


class AstronautListSerializer(serializers.HyperlinkedModelSerializer):
    status = AstronautStatusSerializer(read_only=True)
    agency = serializers.ReadOnlyField(read_only=True, source="agency.name")

    class Meta:
        model = Astronauts
        fields = ('id', 'url', 'name', 'status', 'agency', 'nationality', 'profile_image')


class AstronautNormalSerializer(serializers.HyperlinkedModelSerializer):
    agency = AgencySerializer(read_only=True, many=False)
    status = AstronautStatusSerializer(read_only=True)

    class Meta:
        model = Astronauts
        fields = ('id', 'url', 'name', 'status', 'date_of_birth', 'date_of_death', 'nationality', 'bio', 'twitter',
                  'instagram', 'wiki', 'agency', 'profile_image')
