from api.v350.common.serializers import *


class AstronautDetailedSerializerNoFlights(serializers.HyperlinkedModelSerializer):
    status = AstronautStatusSerializer(read_only=True)
    type = AstronautTypeSerializer(read_only=True)
    agency = AgencySerializer(read_only=True, many=False)

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
    launch_service_provider = AgencySerializerDetailedCommon(many=False, read_only=True)

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


class LaunchListSerializer(serializers.ModelSerializer):
    pad = serializers.StringRelatedField()
    location = serializers.StringRelatedField(source='pad.location')
    status = LaunchStatusSerializer(many=False, read_only=True)
    landing = serializers.SerializerMethodField()
    landing_success = serializers.SerializerMethodField()
    launcher = serializers.SerializerMethodField()
    orbit = serializers.SerializerMethodField()
    mission = serializers.StringRelatedField()
    image = serializers.SerializerMethodField()
    infographic = serializers.SerializerMethodField()
    mission_type = serializers.StringRelatedField(source='mission.mission_type.name')
    slug = serializers.SlugField(source='get_full_absolute_url')

    class Meta:
        model = Launch
        fields = (
            'id', 'url', 'launch_library_id', 'slug', 'name', 'status', 'net', 'window_end', 'window_start', 'mission',
            'mission_type', 'pad', 'location', 'landing', 'landing_success', 'launcher', 'orbit', 'image', 'infographic')

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

    def get_landing(self, obj):
        try:
            cache_key = "%s-%s" % (obj.id, "launch-list-landing")
            landing = cache.get(cache_key)
            if landing is not None:
                return landing

            landings = []
            for stage in obj.rocket.firststage.all():
                if stage.landing is not None:
                    landings.append(stage.landing)

            if len(landings) == 0:
                cache.set(cache_key, None, CACHE_TIMEOUT_TEN_MINUTES)
                return None
            elif len(landings) == 1:
                cache.set(cache_key, landings[0].landing_location.abbrev, CACHE_TIMEOUT_TEN_MINUTES)
                return landings[0].landing_location.abbrev
            elif len(landings) > 1:
                cache.set(cache_key, "MX Landing", CACHE_TIMEOUT_TEN_MINUTES)
                return "MX Landing"
            else:
                cache.set(cache_key, None, CACHE_TIMEOUT_TEN_MINUTES)
                return None

        except Exception as ex:
            return None

    def get_landing_success(self, obj):
        try:
            cache_key = "%s-%s" % (obj.id, "launch-list-landing-success")
            landing = cache.get(cache_key)
            if landing is not None:
                return landing

            landings = []
            for stage in obj.rocket.firststage.all():
                if stage.landing is not None:
                    landings.append(stage.landing)

            if len(landings) == 0:
                cache.set(cache_key, None, CACHE_TIMEOUT_TEN_MINUTES)
                return None
            elif len(landings) == 1:
                landing_status = 0
                if landings[0].success is None:
                    landing_status = 0
                elif landings[0].success:
                    landing_status = 1
                elif not landings[0].success:
                    landing_status = 2
                cache.set(cache_key, landing_status, CACHE_TIMEOUT_TEN_MINUTES)
                return landing_status
            elif len(landings) > 1:
                landing_successes = 0
                landing_failures = 0
                landing_null = 0

                for landing in landings:
                    if landing.success is None:
                        landing_null += 1
                    elif landing.success:
                        landing_successes += 1
                    elif not landing.success:
                        landing_failures += 1

                landing_status = 0
                if (landing_failures > 0 or landing_null > 0) and landing_successes > 0:
                    landing_status = 3
                elif landing_failures > 0 and landing_successes == 0:
                    landing_status = 2
                elif landing_failures == 0 and landing_null == 0 and landing_successes > 0:
                    landing_status = 1
                cache.set(cache_key, landing_status, CACHE_TIMEOUT_TEN_MINUTES)
                return landing_status
            else:
                cache.set(cache_key, None, CACHE_TIMEOUT_TEN_MINUTES)
                return None

        except Exception as ex:
            return None

    def get_launcher(self, obj):
        try:
            cache_key = "%s-%s" % (obj.id, "launch-list-launcher")
            launcher = cache.get(cache_key)
            if launcher is not None:
                return launcher

            launchers = []
            for stage in obj.rocket.firststage.all():
                if stage.launcher is not None:
                    launchers.append(stage.launcher)

            if len(launchers) == 0:
                cache.set(cache_key, None, CACHE_TIMEOUT_ONE_DAY)
                return None
            elif len(launchers) == 1:
                cache.set(cache_key, launchers[0].serial_number, CACHE_TIMEOUT_ONE_DAY)
                return launchers[0].serial_number
            elif len(launchers) > 1:
                cache.set(cache_key, "MX Launchers", CACHE_TIMEOUT_ONE_DAY)
                return "MX Launchers"
            else:
                cache.set(cache_key, None, CACHE_TIMEOUT_ONE_DAY)
                return None

        except Exception as ex:
            return None

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