from drf_queryfields import QueryFieldsMixin

from api.models import *
from rest_framework import serializers

from api.v330.normal.serializers import AgencySerializer, FirstStageSerializer, \
    SecondStageSerializer, PadSerializer, \
    MissionSerializer, LaunchStatusSerializer, OrbiterStatusSerializer

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
        fields = ('id', 'url', 'name', 'description', 'family', 'full_name',
                  'variant', 'alias', 'min_stage', 'max_stage', 'length', 'diameter',
                  'maiden_flight', 'launch_mass', 'leo_capacity', 'gto_capacity',
                  'to_thrust', 'apogee', 'vehicle_range', 'image_url', 'info_url',
                  'wiki_url',)


class OrbiterConfigurationDetailSerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    agency = serializers.ReadOnlyField(read_only=True, source="launch_agency.name")

    class Meta:
        model = OrbiterConfiguration
        fields = ('id', 'url', 'name', 'agency', 'in_use', 'capability', 'history', 'details', 'maiden_flight',
                  'height', 'diameter', 'human_rated', 'crew_capacity', 'payload_capacity', 'flight_life',
                  'image_url', 'nation_url', 'wiki_link', 'info_link')


class AgencySerializerMini(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    parent = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Agency
        fields = ('id', 'url', 'name', 'description', 'parent', 'administrator', 'founding_year', 'type')


class AgencySerializerDetailed(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    parent = serializers.StringRelatedField(read_only=True)
    launcher_list = LauncherConfigDetailSerializerForAgency(many=True, read_only=True)
    orbiter_list = OrbiterConfigurationDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Agency
        fields = ('id', 'url', 'name', 'featured', 'type', 'country_code', 'abbrev', 'description', 'administrator',
                  'founding_year', 'launchers', 'orbiters', 'parent', 'launch_library_url', 'successful_launches',
                  'failed_launches', 'pending_launches', 'info_url', 'wiki_url', 'logo_url', 'image_url', 'nation_url',
                  'launcher_list', 'orbiter_list')

    def get_fields(self):
        fields = super(AgencySerializerDetailed, self).get_fields()
        return fields


class AgencySerializerDetailedForLaunches(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Agency
        fields = ('id', 'url', 'name', 'featured', 'type', 'country_code', 'abbrev', 'description', 'administrator',
                  'founding_year', 'launchers', 'orbiters', 'launch_library_url', 'successful_launches',
                  'failed_launches', 'pending_launches', 'info_url', 'wiki_url', 'logo_url', 'image_url', 'nation_url',)


class AgencySerializerDetailedAndRelated(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    parent = serializers.StringRelatedField(read_only=True)
    launcher_list = LauncherConfigDetailSerializerForAgency(many=True, read_only=True)
    orbiter_list = OrbiterConfigurationDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Agency
        fields = ('id', 'url', 'name', 'featured', 'type', 'country_code', 'abbrev', 'description', 'administrator',
                  'founding_year', 'launchers', 'orbiters', 'parent', 'launch_library_url', 'successful_launches',
                  'failed_launches', 'pending_launches', 'info_url', 'wiki_url', 'logo_url', 'image_url', 'nation_url',
                  'related_agencies', 'launcher_list', 'orbiter_list')

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
        fields = ('id', 'url', 'name', 'description', 'family', 'full_name', 'launch_service_provider',
                  'variant', 'alias', 'min_stage', 'max_stage', 'length', 'diameter',
                  'maiden_flight', 'launch_mass', 'leo_capacity', 'gto_capacity',
                  'to_thrust', 'apogee', 'vehicle_range', 'image_url', 'info_url',
                  'wiki_url',)


class AstronautStatusDetailedSerilizer(serializers.ModelSerializer):
    class Meta:
        model = AstronautStatus
        fields = ('name', )


class AstronautDetailedSerializer(serializers.ModelSerializer):
    status = AstronautStatusDetailedSerilizer(read_only=True, many=False)
    agency = AgencySerializer(read_only=True, many=False)

    class Meta:
        model = Astronauts
        fields = ('name', 'date_of_birth', 'date_of_death', 'nationality',
                  'agency', 'twitter', 'instagram', 'bio', 'status', 'profile_image',
                  'wiki', 'flights')


class OrbiterDetailedSerializer(serializers.ModelSerializer):
    status = OrbiterStatusSerializer(read_only=True, many=False)
    orbiter_config = OrbiterConfigurationDetailSerializer(read_only=True,
                                                          many=False)

    class Meta:
        model = Orbiter
        fields = ('name', 'serial_number', 'status',
                  'orbiter_config')


class OrbiterFlightDetailedSerializer(serializers.ModelSerializer):
    launch_crew = AstronautDetailedSerializer(read_only=True, many=True)
    onboard_crew = AstronautDetailedSerializer(read_only=True, many=True)
    landing_crew = AstronautDetailedSerializer(read_only=True, many=True)
    orbiter = OrbiterDetailedSerializer(read_only=True, many=False)

    class Meta:
        model = OrbiterFlight
        fields = ('splashdown', 'launch_crew', 'onboard_crew', 'landing_crew',
                  'orbiter', 'destination')


class SpaceStationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpaceStationStatus
        fields = ('name',)


class SpaceStationDetailedSerializer(serializers.ModelSerializer):
    docked_vehicles = OrbiterDetailedSerializer(read_only=True, many=True)
    crew = AstronautDetailedSerializer(read_only=True, many=True)
    status = SpaceStationStatusSerializer(read_only=True, many=False)
    owner = AgencySerializerDetailed(read_only=True, many=False)

    class Meta:
        model = SpaceStation
        fields = ('name', 'founded', 'docked_vehicles', 'description', 'orbit',
                  'crew', 'status', 'owner')


class RocketDetailedSerializer(serializers.ModelSerializer):
    configuration = LauncherConfigDetailSerializer(read_only=True, many=False)
    first_stage = FirstStageSerializer(read_only=True, many=True, source='firststage')
    second_stage = SecondStageSerializer(read_only=True, many=False, source='secondstage')
    orbiter_flight = OrbiterFlightDetailedSerializer(read_only=True, many=False, source='orbiterflight')

    class Meta:
        model = Rocket
        fields = ('configuration', 'first_stage', 'second_stage', 'orbiter_flight')


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
        fields = ('id', 'url', 'slug', 'name', 'img_url', 'status', 'net', 'window_end', 'window_start', 'inhold',
                  'tbdtime', 'tbddate', 'probability', 'holdreason', 'failreason', 'hashtag', 'rocket',
                  'mission', 'pad', 'infoURLs', 'vidURLs')
