from api.v340.common.serializers import *


class AstronautDetailedSerializerNoFlights(serializers.HyperlinkedModelSerializer):
    status = AstronautStatusSerializer(read_only=True)
    type = AstronautTypeSerializer(read_only=True)
    agency = AgencySerializerMini(read_only=True, many=False)

    class Meta:
        model = Astronaut
        # fields = ('name',)
        fields = ('id', 'url', 'name', 'status', 'type', 'agency', 'date_of_birth', 'date_of_death', 'nationality',
                  'twitter', 'instagram', 'bio', 'profile_image', 'wiki',)


class AstronautFlightSerializer(serializers.ModelSerializer):
    role = serializers.StringRelatedField(read_only=True, source='role.role')
    astronaut = AstronautDetailedSerializerNoFlights(read_only=True, many=False)

    class Meta:
        model = AstronautFlight
        fields = ('role', 'astronaut')


class LandingSerializer(serializers.ModelSerializer):
    type = LandingTypeSerializer(many=False, read_only=True, source='landing_type')
    location = LandingLocationSerializer(many=False, read_only=True, source='landing_location')

    class Meta:
        model = Landing
        fields = ('attempt', 'success', 'description', 'location', 'type')


class LauncherDetailedSerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Launcher
        fields = ('id', 'url', 'details', 'flight_proven', 'serial_number', 'status', 'previous_flights', 'image_url')


class FirstStageSerializer(serializers.ModelSerializer):
    type = serializers.StringRelatedField()
    launcher = LauncherDetailedSerializer(read_only=True, many=False)
    landing = LandingSerializer(read_only=True, many=False)

    class Meta:
        model = FirstStage
        fields = ('type', 'reused', 'launcher_flight_number', 'launcher', 'landing',)


class LauncherConfigDetailSerializer(QueryFieldsMixin, serializers.ModelSerializer):
    manufacturer = AgencySerializer(many=False, read_only=True)

    def get_rep(self, obj):
        rep = obj.rep
        serializer_context = {'request': self.context.get('request'),
                              'id': obj.id}
        serializer = AgencySerializer(rep, context=serializer_context)
        return serializer.data

    class Meta:
        model = LauncherConfig
        fields = ('id', 'launch_library_id', 'url', 'name', 'description', 'family', 'full_name', 'manufacturer',
                  'variant', 'alias', 'min_stage', 'max_stage', 'length', 'diameter',
                  'maiden_flight', 'launch_mass', 'leo_capacity', 'gto_capacity',
                  'to_thrust', 'apogee', 'vehicle_range', 'image_url', 'info_url',
                  'wiki_url',)


class LauncherConfigSerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    manufacturer = AgencySerializerMini(read_only=True)

    class Meta:
        model = LauncherConfig
        fields = ('id', 'launch_library_id', 'url', 'name', 'manufacturer',)


class SpacecraftDetailedNoFlightsSerializer(serializers.HyperlinkedModelSerializer):
    status = SpacecraftStatusSerializer(read_only=True, many=False)
    spacecraft_config = SpacecraftConfigurationDetailSerializer(read_only=True, many=False)

    class Meta:
        model = Spacecraft
        fields = ('id', 'url', 'name', 'serial_number', 'status', 'description', 'spacecraft_config',)


class DockingEventSerializerForSpacecraftFlight(serializers.ModelSerializer):
    docking_location = serializers.StringRelatedField(many=False, read_only=True)
    spacestation = SpaceStationSerializerForCommon(many=False, read_only=True, source='space_station')

    class Meta:
        model = DockingEvent
        fields = ('id', 'url', 'spacestation', 'docking', 'departure', 'docking_location')


class SpacecraftFlightDetailedSerializerForLaunch(serializers.HyperlinkedModelSerializer):
    launch_crew = AstronautFlightSerializer(read_only=True, many=True)
    onboard_crew = AstronautFlightSerializer(read_only=True, many=True)
    landing_crew = AstronautFlightSerializer(read_only=True, many=True)
    spacecraft = SpacecraftDetailedNoFlightsSerializer(read_only=True, many=False)
    docking_events = DockingEventSerializerForSpacecraftFlight(read_only=True, many=True)
    id = serializers.IntegerField(source='pk')

    class Meta:
        model = SpacecraftFlight
        fields = ('id', 'url', 'mission_end', 'destination', 'launch_crew', 'onboard_crew', 'landing_crew', 'spacecraft',
                  'docking_events')


class SpacecraftFlightSerializerForLaunch(serializers.HyperlinkedModelSerializer):
    spacecraft = SpacecraftSerializer(read_only=True, many=False)

    class Meta:
        model = SpacecraftFlight
        fields = ('id', 'url', 'destination', 'mission_end', 'spacecraft',)


class AgencySerializerDetailedForLaunches(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Agency
        fields = ('id', 'url', 'name', 'featured', 'type', 'country_code', 'abbrev', 'description', 'administrator',
                  'founding_year', 'launchers', 'spacecraft', 'launch_library_url', 'successful_launches',
                  'failed_launches', 'pending_launches', 'info_url', 'wiki_url', 'logo_url', 'image_url', 'nation_url',)


class RocketDetailedSerializer(serializers.ModelSerializer):
    configuration = LauncherConfigDetailSerializer(read_only=True, many=False)
    launcher_stage = FirstStageSerializer(read_only=True, many=True, source='firststage')
    spacecraft_stage = SpacecraftFlightDetailedSerializerForLaunch(read_only=True, many=False, source='spacecraftflight')

    class Meta:
        model = Rocket
        fields = ('configuration', 'launcher_stage', 'spacecraft_stage')


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

    infoURLs = serializers.StringRelatedField(read_only=True, many=True, source='info_urls')
    vidURLs = serializers.StringRelatedField(read_only=True, many=True, source='vid_urls')

    image = serializers.SerializerMethodField()
    infographic = serializers.SerializerMethodField()

    class Meta:
        depth = 3
        model = Launch
        fields = ('id', 'url', 'launch_library_id', 'slug', 'name', 'status', 'net', 'window_end', 'window_start', 'inhold',
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
        fields = ('id', 'url', 'launch_library_id', 'slug', 'name', 'status', 'net', 'window_end', 'window_start', 'inhold',
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