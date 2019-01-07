from api.v330.common.serializers import *


class LaunchListSerializerForAstronaut(serializers.ModelSerializer):
    pad = PadSerializerMini(read_only=True, many=False)
    status = LaunchStatusSerializer(many=False, read_only=True)
    orbit = serializers.SerializerMethodField()
    mission = MissionSerializerMini(read_only=True, many=False)
    slug = serializers.SlugField(source='get_full_absolute_url')

    class Meta:
        model = Launch
        fields = ('id', 'url', 'launch_library_id', 'slug', 'name', 'status', 'net', 'window_end', 'window_start',
                  'mission', 'pad', 'orbit')

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


class AstronautDetailedSerializer(serializers.HyperlinkedModelSerializer):
    status = AstronautStatusSerializer(read_only=True)
    agency = AgencySerializerMini(read_only=True, many=False)
    flights = LaunchListSerializerForAstronaut(read_only=True, many=True)

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
