from sorl_thumbnail_serializer.fields import HyperlinkedSorlImageField

from api.v340.common.serializers import *


class LaunchListSerializerForAstronaut(serializers.ModelSerializer):
    pad = PadSerializerMini(read_only=True, many=False)
    status = LaunchStatusSerializer(many=False, read_only=True)
    orbit = serializers.SerializerMethodField()
    mission = MissionSerializerMini(read_only=True, many=False)
    slug = serializers.SlugField(source='get_full_absolute_url')
    rocket = RocketSerializerMini(read_only=True, many=False)

    class Meta:
        model = Launch
        fields = ('id', 'url', 'launch_library_id', 'slug', 'name', 'status', 'net', 'window_end', 'window_start',
                  'mission', 'pad', 'orbit', 'rocket')

    def get_orbit(self, obj):
        try:
            cache_key = "%s-%s" % (obj.id, "launch-list-orbit")
            orbit = cache.get(cache_key)
            if orbit is not None:
                return orbit

            if obj.mission.orbit is not None and obj.mission.orbit.abbrev is not None:
                cache.set(cache_key, obj.mission.orbit.abbrev, CACHE_TIMEOUT_ONE_DAY)
                return obj.mission.orbit.abbrev

        except Exception as ex:
            return None


class AstronautDetailedWithLaunchListSerializer(serializers.HyperlinkedModelSerializer):
    status = AstronautStatusSerializer(read_only=True)
    type = AstronautTypeSerializer(read_only=True)
    agency = AgencySerializerDetailedForLaunches(read_only=True, many=False)
    flights = LaunchListSerializer(read_only=True, many=True)
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


class AstronautDetailedSerializer(serializers.HyperlinkedModelSerializer):
    status = AstronautStatusSerializer(read_only=True)
    type = AstronautTypeSerializer(read_only=True)
    agency = AgencySerializerMini(read_only=True, many=False)
    flights = LaunchListSerializerForAstronaut(read_only=True, many=True)
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
