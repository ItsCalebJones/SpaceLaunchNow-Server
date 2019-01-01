from drf_queryfields import QueryFieldsMixin

from api.models import *
from rest_framework import serializers

from api.v330.list.serializers import LaunchListSerializer
from api.v330.normal.serializers import AgencySerializer, FirstStageSerializer, \
    SecondStageSerializer, PadSerializer, \
    MissionSerializer, LaunchStatusSerializer, SpacecraftStatusSerializer, SpacecraftFlightSerializer, \
    AstronautStatusSerializer, SpaceStationStatusSerializer

CACHE_TIMEOUT_ONE_DAY = 24 * 60 * 60


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
                  'to_thrust', 'apogee', 'vehicle_range', 'image_url', 'info_url',
                  'wiki_url',)


class SpacecraftConfigurationDetailSerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    agency = serializers.ReadOnlyField(read_only=True, source="launch_agency.name")

    class Meta:
        model = SpacecraftConfiguration
        fields = ('id', 'url', 'name', 'agency', 'in_use', 'capability', 'history', 'details', 'maiden_flight',
                  'height', 'diameter', 'human_rated', 'crew_capacity', 'payload_capacity', 'flight_life',
                  'image_url', 'nation_url', 'wiki_link', 'info_link')


class AgencySerializerMini(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Agency
        fields = ('id', 'url', 'name', 'type')


class AgencySerializerDetailed(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    parent = serializers.StringRelatedField(read_only=True)
    launcher_list = LauncherConfigDetailSerializerForAgency(many=True, read_only=True)
    spacecraft_list = SpacecraftConfigurationDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Agency
        fields = ('id', 'url', 'name', 'featured', 'type', 'country_code', 'abbrev', 'description', 'administrator',
                  'founding_year', 'launchers', 'spacecraft', 'parent', 'launch_library_url', 'successful_launches',
                  'failed_launches', 'pending_launches', 'info_url', 'wiki_url', 'logo_url', 'image_url', 'nation_url',
                  'launcher_list', 'spacecraft_list')

    def get_fields(self):
        fields = super(AgencySerializerDetailed, self).get_fields()
        return fields


class AgencySerializerDetailedForLaunches(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Agency
        fields = ('id', 'url', 'name', 'featured', 'type', 'country_code', 'abbrev', 'description', 'administrator',
                  'founding_year', 'launchers', 'spacecraft', 'launch_library_url', 'successful_launches',
                  'failed_launches', 'pending_launches', 'info_url', 'wiki_url', 'logo_url', 'image_url', 'nation_url',)


class AgencySerializerDetailedAndRelated(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    parent = serializers.StringRelatedField(read_only=True)
    launcher_list = LauncherConfigDetailSerializerForAgency(many=True, read_only=True)
    spacecraft_list = SpacecraftConfigurationDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Agency
        fields = ('id', 'url', 'name', 'featured', 'type', 'country_code', 'abbrev', 'description', 'administrator',
                  'founding_year', 'launchers', 'spacecraft', 'parent', 'launch_library_url', 'successful_launches',
                  'failed_launches', 'pending_launches', 'info_url', 'wiki_url', 'logo_url', 'image_url', 'nation_url',
                  'related_agencies', 'launcher_list', 'spacecraft_list')

    def get_fields(self):
        fields = super(AgencySerializerDetailedAndRelated, self).get_fields()
        fields['related_agencies'] = AgencySerializerDetailed(many=True)
        return fields


class LauncherConfigDetailSerializer(QueryFieldsMixin, serializers.ModelSerializer):
    launch_service_provider = AgencySerializerDetailedForLaunches(many=False, read_only=True, source='launch_agency')

    def get_rep(self, obj):
        rep = obj.rep
        serializer_context = {'request': self.context.get('request'),
                              'id': obj.id}
        serializer = AgencySerializer(rep, context=serializer_context)
        return serializer.data

    class Meta:
        model = LauncherConfig
        fields = ('id', 'launch_library_id', 'url', 'name', 'description', 'family', 'full_name', 'launch_service_provider',
                  'variant', 'alias', 'min_stage', 'max_stage', 'length', 'diameter',
                  'maiden_flight', 'launch_mass', 'leo_capacity', 'gto_capacity',
                  'to_thrust', 'apogee', 'vehicle_range', 'image_url', 'info_url',
                  'wiki_url',)


class AstronautDetailedSerializer(serializers.HyperlinkedModelSerializer):
    status = AstronautStatusSerializer(read_only=True)
    agency = AgencySerializerMini(read_only=True, many=False)
    flights = LaunchListSerializer(read_only=True, many=True)

    class Meta:
        model = Astronauts
        # fields = ('name',)
        fields = ('id', 'url', 'name', 'status', 'agency', 'date_of_birth', 'date_of_death', 'nationality',
                  'twitter', 'instagram', 'bio', 'profile_image', 'wiki', 'flights')


class AstronautDetailedSerializerNoFlights(serializers.HyperlinkedModelSerializer):
    status = AstronautStatusSerializer(read_only=True)
    agency = AgencySerializerMini(read_only=True, many=False)

    class Meta:
        model = Astronauts
        # fields = ('name',)
        fields = ('id', 'url', 'name', 'status', 'agency', 'date_of_birth', 'date_of_death', 'nationality',
                  'twitter', 'instagram', 'bio', 'profile_image', 'wiki',)


class AstronautSerializer(serializers.HyperlinkedModelSerializer):
    status = AstronautStatusSerializer(read_only=True)
    agency = serializers.StringRelatedField(read_only=True, source='agency.name')

    class Meta:
        model = Astronauts
        fields = ('id', 'url', 'name', 'status', 'agency', 'profile_image')


class AstronautFlightSerializer(serializers.ModelSerializer):
    role = serializers.StringRelatedField(read_only=True, source='role.role')
    astronaut = AstronautDetailedSerializerNoFlights(read_only=True, many=False)

    class Meta:
        model = AstronautFlight
        fields = ('role', 'astronaut')


class AstronautFlightForExpeditionSerializer(serializers.ModelSerializer):
    role = serializers.StringRelatedField(read_only=True, source='role.role')
    astronaut = AstronautSerializer(read_only=True, many=False)

    class Meta:
        model = AstronautFlight
        fields = ('role', 'astronaut')


class AgencyListSerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Agency
        fields = ('id', 'url', 'name', 'abbrev',)


class SpaceStationDetailedSerializerForExpedition(serializers.HyperlinkedModelSerializer):
    status = SpaceStationStatusSerializer(read_only=True, many=False)
    owners = AgencyListSerializer(read_only=True, many=False)
    orbit = serializers.StringRelatedField(many=False, read_only=True)

    class Meta:
        model = SpaceStation
        fields = ('id', 'url', 'name', 'status', 'founded', 'description', 'orbit', 'owners',)


class ExpeditionDetailSerializer(serializers.HyperlinkedModelSerializer):
    crew = AstronautFlightForExpeditionSerializer(many=True, read_only=True)
    spacestation = SpaceStationDetailedSerializerForExpedition(many=False, read_only=True, source='space_station')

    class Meta:
        model = Expedition
        fields = ('id', 'url', 'name', 'start', 'end', 'spacestation', 'crew')


class SpacecraftDetailedSerializer(serializers.HyperlinkedModelSerializer):
    status = serializers.StringRelatedField(source='status.name', read_only=True, many=False)
    spacecraft_config = SpacecraftConfigurationDetailSerializer(read_only=True, many=False)
    flights = SpacecraftFlightSerializer(read_only=True, many=True, source='spacecraftflight')

    class Meta:
        model = Spacecraft
        fields = ('id', 'url', 'name', 'serial_number', 'status', 'spacecraft_config', 'flights')


class SpacecraftDetailedNoFlightsSerializer(serializers.HyperlinkedModelSerializer):
    status = serializers.StringRelatedField(source='status.name', read_only=True, many=False)
    spacecraft_config = SpacecraftConfigurationDetailSerializer(read_only=True, many=False)

    class Meta:
        model = Spacecraft
        fields = ('id', 'url', 'name', 'serial_number', 'status', 'spacecraft_config',)


class SpacecraftFlightSerializer(serializers.HyperlinkedModelSerializer):
    spacecraft = serializers.StringRelatedField(read_only=True, many=False)

    class Meta:
        model = SpacecraftFlight
        fields = ('id', 'url', 'destination', 'splashdown', 'spacecraft')


class DockingEventDetailedSerializerForSpacestation(serializers.HyperlinkedModelSerializer):
    flight_vehicle = serializers.StringRelatedField(read_only=True, many=False)
    docking_location = serializers.StringRelatedField(many=False, read_only=True)

    class Meta:
        model = DockingEvent
        fields = ('id', 'url', 'docking', 'departure', 'flight_vehicle', 'docking_location')


class DockingEventDetailedSerializer(serializers.HyperlinkedModelSerializer):
    flight_vehicle = SpacecraftFlightSerializer(read_only=True, many=False)
    docking_location = serializers.StringRelatedField(many=False, read_only=True)

    class Meta:
        model = DockingEvent
        fields = ('id', 'url', 'docking', 'departure', 'flight_vehicle', 'docking_location')


class SpaceStationSerializerForDockingEvent(serializers.HyperlinkedModelSerializer):
    status = SpaceStationStatusSerializer(read_only=True, many=False)
    orbit = serializers.StringRelatedField(many=False, read_only=True)

    class Meta:
        model = SpaceStation
        fields = ('id', 'url', 'name', 'status', 'founded', 'description', 'orbit',)


class DockingEventSerializerForSpacecraftFlight(serializers.ModelSerializer):
    docking_location = serializers.StringRelatedField(many=False, read_only=True)
    spacestation = SpaceStationSerializerForDockingEvent(many=False, read_only=True, source='space_station')

    class Meta:
        model = DockingEvent
        fields = ('spacestation', 'docking', 'departure', 'docking_location')


class SpacecraftFlightDetailedSerializer(serializers.HyperlinkedModelSerializer):
    launch_crew = AstronautFlightSerializer(read_only=True, many=True)
    onboard_crew = AstronautFlightSerializer(read_only=True, many=True)
    landing_crew = AstronautFlightSerializer(read_only=True, many=True)
    spacecraft = SpacecraftDetailedNoFlightsSerializer(read_only=True, many=False)
    docking_events = DockingEventSerializerForSpacecraftFlight(read_only=True, many=True)
    launch = LaunchListSerializer(read_only=True, many=False, source='rocket.launch')
    id = serializers.IntegerField(source='pk')

    class Meta:
        model = SpacecraftFlight
        fields = ('id', 'url', 'splashdown', 'destination', 'launch_crew', 'onboard_crew', 'landing_crew', 'spacecraft', 'launch', 'docking_events')


class ExpeditionSerializerForSpacestation(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Expedition
        fields = ('id', 'url', 'name', 'start', 'end',)


class SpaceStationDetailedSerializer(serializers.HyperlinkedModelSerializer):
    status = SpaceStationStatusSerializer(read_only=True, many=False)
    owners = AgencySerializer(read_only=True, many=True)
    orbit = serializers.StringRelatedField(many=False, read_only=True)
    docking_events = DockingEventDetailedSerializerForSpacestation(read_only=True, many=True)
    expedition = ExpeditionSerializerForSpacestation(read_only=True, many=True)

    class Meta:
        model = SpaceStation
        fields = ('id', 'url', 'name', 'status', 'founded', 'description', 'orbit', 'owners', 'docking_events', 'expedition')


class RocketDetailedSerializer(serializers.ModelSerializer):
    configuration = LauncherConfigDetailSerializer(read_only=True, many=False)
    launcher_stage = FirstStageSerializer(read_only=True, many=True, source='firststage')
    spacecraft_stage = SpacecraftFlightDetailedSerializer(read_only=True, many=False, source='spacecraftflight')

    class Meta:
        model = Rocket
        fields = ('configuration', 'launcher_stage', 'spacecraft_stage')


class LaunchDetailedSerializer(serializers.HyperlinkedModelSerializer):
    pad = PadSerializer(many=False, read_only=True)
    rocket = RocketDetailedSerializer(many=False, read_only=True)
    mission = MissionSerializer(many=False, read_only=True)
    status = LaunchStatusSerializer(many=False, read_only=True)
    slug = serializers.SlugField(source='get_full_absolute_url')

    infoURLs = serializers.StringRelatedField(read_only=True, many=True, source='info_urls')
    vidURLs = serializers.StringRelatedField(read_only=True, many=True, source='vid_urls')

    class Meta:
        depth = 3
        model = Launch
        fields = ('id', 'url', 'launch_library_id', 'slug', 'name', 'img_url', 'status', 'net', 'window_end', 'window_start', 'inhold',
                  'tbdtime', 'tbddate', 'probability', 'holdreason', 'failreason', 'hashtag', 'rocket',
                  'mission', 'pad', 'infoURLs', 'vidURLs')
