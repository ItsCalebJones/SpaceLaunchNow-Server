from sorl_thumbnail_serializer.fields import HyperlinkedSorlImageField

from api.v350.common.serializers import *


class AstronautDetailedSerializer(serializers.HyperlinkedModelSerializer):
    status = AstronautStatusSerializer(read_only=True)
    type = AstronautTypeSerializer(read_only=True)
    agency = AgencySerializerMini(read_only=True, many=False)
    flights = LaunchSerializerCommon(read_only=True, many=True)
    landings = SpacecraftFlightSerializer(read_only=True, many=True)
    # A thumbnail image, sorl options and read-only
    profile_image_thumbnail = HyperlinkedSorlImageField(
        '128x128',
        options={"crop": "80% top"},
        source='profile_image',
        read_only=True
    )

    class Meta:
        model = Astronaut
        # fields = ('name',)
        fields = ('id', 'url', 'name', 'status', 'type', 'agency', 'date_of_birth', 'date_of_death', 'nationality',
                  'twitter', 'instagram', 'bio', 'profile_image', 'profile_image_thumbnail', 'wiki', 'flights',
                  'landings', 'last_flight', 'first_flight',)


class AstronautListSerializer(serializers.HyperlinkedModelSerializer):
    status = AstronautStatusSerializer(read_only=True)
    type = AstronautTypeSerializer(read_only=True)
    agency = serializers.ReadOnlyField(read_only=True, source="agency.name")
    # A thumbnail image, sorl options and read-only
    profile_image_thumbnail = HyperlinkedSorlImageField(
        '128x128',
        options={"crop": "80% top"},
        source='profile_image',
        read_only=True
    )

    class Meta:
        model = Astronaut
        fields = ('id', 'url', 'name', 'status', 'type', 'agency', 'nationality', 'profile_image', 'profile_image_thumbnail')


class AstronautNormalSerializer(serializers.HyperlinkedModelSerializer):
    agency = AgencySerializer(read_only=True, many=False)
    status = AstronautStatusSerializer(read_only=True)
    type = AstronautTypeSerializer(read_only=True)
    profile_image_thumbnail = HyperlinkedSorlImageField(
        '128x128',
        options={"crop": "80% top"},
        source='profile_image',
        read_only=True
    )

    class Meta:
        model = Astronaut
        fields = ('id', 'url', 'name', 'status', 'type', 'date_of_birth', 'date_of_death', 'nationality', 'bio', 'twitter',
                  'instagram', 'wiki', 'agency', 'profile_image', 'profile_image_thumbnail', 'last_flight', 'first_flight',)
