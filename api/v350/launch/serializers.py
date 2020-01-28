from api.v350.common.serializers import *


class AstronautDetailedSerializerNoFlights(serializers.HyperlinkedModelSerializer):
    status = AstronautStatusSerializer(read_only=True)
    type = AstronautTypeSerializer(read_only=True)
    agency = AgencySerializerMini(read_only=True, many=False)

    class Meta:
        model = Astronaut
        # fields = ('name',)
        fields = ('id', 'url', 'name', 'status', 'type', 'agency', 'date_of_birth', 'date_of_death', 'nationality',
                  'twitter', 'instagram', 'bio', 'profile_image', 'wiki', 'last_flight',  'first_flight',)


class LandingSerializer(serializers.ModelSerializer):
    type = LandingTypeSerializer(many=False, read_only=True, source='landing_type')
    location = LandingLocationSerializer(many=False, read_only=True, source='landing_location')

    class Meta:
        model = Landing
        fields = ('id', 'attempt', 'success', 'description', 'location', 'type')


class LauncherDetailedSerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Launcher
        fields = ('id', 'url', 'details', 'flight_proven', 'serial_number', 'status', 'image_url',
                  'successful_landings', 'attempted_landings', 'flights', 'last_launch_date', 'first_launch_date')


class LaunchSerializerMini(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Launch
        fields = ('id', 'name')


class FirstStageSerializer(serializers.ModelSerializer):
    type = serializers.StringRelatedField()
    launcher = LauncherDetailedSerializer(read_only=True, many=False)
    landing = LandingSerializer(read_only=True, many=False)
    previous_flight = LaunchSerializerMini(read_only=True, many=False)

    class Meta:
        model = FirstStage
        fields = ('id', 'type', 'reused', 'launcher_flight_number', 'launcher', 'landing', 'previous_flight_date',
                  'turn_around_time_days', 'previous_flight')


class SpacecraftFlightDetailedSerializerForLaunch(serializers.HyperlinkedModelSerializer):
    launch_crew = AstronautFlightSerializer(read_only=True, many=True)
    onboard_crew = AstronautFlightSerializer(read_only=True, many=True)
    landing_crew = AstronautFlightSerializer(read_only=True, many=True)
    spacecraft = SpacecraftDetailedNoFlightsSerializer(read_only=True, many=False)
    docking_events = DockingEventSerializerForSpacecraftFlight(read_only=True, many=True)
    id = serializers.IntegerField(source='pk')

    class Meta:
        model = SpacecraftFlight
        fields = (
            'id', 'url', 'mission_end', 'destination', 'launch_crew', 'onboard_crew', 'landing_crew', 'spacecraft',
            'docking_events')


class SpacecraftFlightSerializerForLaunch(serializers.HyperlinkedModelSerializer):
    spacecraft = SpacecraftSerializer(read_only=True, many=False)

    class Meta:
        model = SpacecraftFlight
        fields = ('id', 'url', 'destination', 'mission_end', 'spacecraft',)


class RocketDetailedSerializer(serializers.ModelSerializer):
    configuration = LauncherConfigDetailSerializer(read_only=True, many=False)
    launcher_stage = FirstStageSerializer(read_only=True, many=True, source='firststage')
    spacecraft_stage = SpacecraftFlightDetailedSerializerForLaunch(read_only=True, many=False,
                                                                   source='spacecraftflight')

    class Meta:
        model = Rocket
        fields = ('id', 'configuration', 'launcher_stage', 'spacecraft_stage')


class RocketSerializer(serializers.ModelSerializer):
    configuration = LauncherConfigSerializer(read_only=True, many=False)
    launcher_stage = FirstStageSerializer(read_only=True, many=True, source='firststage')
    spacecraft_stage = SpacecraftFlightSerializerForLaunch(read_only=True, many=False, source='spacecraftflight')

    class Meta:
        model = Rocket
        fields = ('id', 'configuration', 'launcher_stage', 'spacecraft_stage')


class LaunchDetailedSerializer(serializers.HyperlinkedModelSerializer):
    pad = PadSerializer(many=False, read_only=True)
    rocket = RocketDetailedSerializer(many=False, read_only=True)
    mission = MissionSerializer(many=False, read_only=True)
    status = LaunchStatusSerializer(many=False, read_only=True)
    slug = serializers.SlugField(source='get_full_absolute_url')
    launch_service_provider = AgencySerializerDetailedForLaunches(many=False, read_only=True)

    infoURLs = InfoURLSerializer(read_only=True, many=True, source='info_urls')
    vidURLs = VidURLSerializer(read_only=True, many=True, source='vid_urls')

    image = serializers.SerializerMethodField()
    infographic = serializers.SerializerMethodField()

    class Meta:
        depth = 3
        model = Launch
        fields = (
            'id', 'url', 'launch_library_id', 'slug', 'name', 'status', 'net', 'window_end', 'window_start', 'inhold',
            'tbdtime', 'tbddate', 'probability', 'holdreason', 'failreason', 'hashtag', 'launch_service_provider',
            'rocket', 'mission', 'pad', 'infoURLs', 'vidURLs', 'image', 'infographic', 'orbital_launch_attempt_count',
            'location_launch_attempt_count', 'pad_launch_attempt_count', 'agency_launch_attempt_count',
            'orbital_launch_attempt_count_year', 'location_launch_attempt_count_year', 'pad_launch_attempt_count_year',
            'agency_launch_attempt_count_year')

    def get_image(self, obj):
        if obj.image_url:
            return obj.image_url.url
        elif obj.rocket and obj.rocket.configuration.image_url:
            return obj.rocket.configuration.image_url.url
        else:
            return None

    def get_infographic(self, obj):
        if obj.infographic_url:
            return obj.infographic_url.url
        else:
            return None


class LaunchSerializer(serializers.HyperlinkedModelSerializer):
    pad = PadSerializer(many=False, read_only=True)
    rocket = RocketSerializer(many=False, read_only=True)
    mission = MissionSerializer(many=False, read_only=True)
    status = LaunchStatusSerializer(many=False, read_only=True)
    slug = serializers.SlugField(source='get_full_absolute_url')
    launch_service_provider = AgencySerializerMini(read_only=True)

    infoURLs = serializers.ReadOnlyField()
    vidURLs = serializers.ReadOnlyField()

    image = serializers.SerializerMethodField()
    infographic = serializers.SerializerMethodField()

    class Meta:
        depth = 3
        model = Launch
        fields = (
            'id', 'url', 'launch_library_id', 'slug', 'name', 'status', 'net', 'window_end', 'window_start', 'inhold',
            'tbdtime', 'tbddate', 'probability', 'holdreason', 'failreason', 'hashtag', 'launch_service_provider',
            'rocket', 'mission', 'pad', 'infoURLs', 'vidURLs', 'image', 'infographic')

    def get_image(self, obj):
        if obj.image_url:
            return obj.image_url.url
        elif obj.rocket.configuration.image_url:
            return obj.rocket.configuration.image_url.url
        else:
            return None

    def get_infographic(self, obj):
        if obj.infographic_url:
            return obj.infographic_url.url
        else:
            return None
