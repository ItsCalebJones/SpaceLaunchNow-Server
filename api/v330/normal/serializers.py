from drf_queryfields import QueryFieldsMixin
from zinnia.models import Entry

from api.models import *
from rest_framework import serializers


class AgencySerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    parent = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Agency
        fields = ('id', 'url', 'name', 'featured', 'type', 'country_code', 'abbrev', 'description', 'administrator',
                  'founding_year', 'launchers', 'spacecraft', 'parent', )


class LauncherConfigSerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    launch_service_provider = serializers.ReadOnlyField(read_only=True, source="launch_agency.name")

    class Meta:
        model = LauncherConfig
        fields = ('id', 'url', 'name', 'launch_service_provider',)


class LauncherSerializer(QueryFieldsMixin, serializers.ModelSerializer):

    class Meta:
        model = Launcher
        fields = ('id', 'url', 'flight_proven', 'serial_number',)


class SpacecraftConfigSerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SpacecraftConfiguration
        fields = ('id', 'url', 'name', 'in_use')


class EventsSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Events
        fields = ('id', 'url', 'name', 'description', 'location', 'feature_image', 'date')


class LocationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Location
        fields = ('id', 'name', 'country_code',)


class PadSerializer(serializers.ModelSerializer):
    location = LocationSerializer(many=False)

    class Meta:
        model = Pad
        fields = ('id', 'agency_id', 'name', 'info_url', 'wiki_url', 'map_url', 'latitude', 'longitude', 'location')


class LaunchStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = LaunchStatus
        fields = ('id', 'name',)


class LSPSerializer(serializers.ModelSerializer):
    parent = serializers.StringRelatedField(read_only=True)
    type = serializers.StringRelatedField(many=False, source='agency_type')

    class Meta:
        model = Agency
        fields = ('id', 'name', 'parent', 'country_code', 'abbrev', 'type', 'info_url', 'wiki_url')


class MissionSerializer(serializers.ModelSerializer):
    type = serializers.StringRelatedField(many=False, source='mission_type')
    orbit = serializers.StringRelatedField(many=False)
    orbit_abbrev = serializers.StringRelatedField(many=False, source='orbit.abbrev')

    class Meta:
        model = Mission
        fields = ('id', 'name', 'description', 'type', 'orbit', 'orbit_abbrev')


class LandingTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandingType
        fields = ('name', 'abbrev', 'description',)


class LandingLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandingLocation
        fields = ('name', 'abbrev', 'description',)


class LandingSerializer(serializers.ModelSerializer):
    type = LandingTypeSerializer(many=False, read_only=True, source='landing_type')
    location = LandingLocationSerializer(many=False, read_only=True, source='landing_location')

    class Meta:
        model = Landing
        fields = ('attempt', 'success', 'description', 'location', 'type')


class LauncherDetailedSerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Launcher
        fields = ('id', 'url', 'details', 'flight_proven', 'serial_number', 'status', 'previous_flights',)


class FirstStageSerializer(serializers.ModelSerializer):
    type = serializers.StringRelatedField()
    launcher = LauncherDetailedSerializer(read_only=True, many=False)
    landing = LandingSerializer(read_only=True, many=False)

    class Meta:
        model = FirstStage
        fields = ('type', 'reused', 'launcher_flight_number', 'launcher', 'landing',)


class SecondStageSerializer(serializers.ModelSerializer):
    launcher = LauncherDetailedSerializer(read_only=True, many=False)
    landing = LandingSerializer(read_only=True, many=False)

    class Meta:
        model = SecondStage
        fields = ('launcher', 'landing',)


class AstronautStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = AstronautStatus
        fields = ('id', 'name', )


class AstronautSerializer(serializers.ModelSerializer):
    status = AstronautStatusSerializer(read_only=True, many=False)
    agency = serializers.StringRelatedField(read_only=True, source='agency.name')

    class Meta:
        model = Astronauts
        # fields = ('name',)
        fields = ('name', 'status', 'agency', 'profile_image')


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AstronautRole
        fields = ('name',)


class AstronautFlightSerializer(serializers.ModelSerializer):
    role = serializers.StringRelatedField(read_only=True, source='role.role')
    astronaut = AstronautSerializer(read_only=True, many=False)

    class Meta:
        model = AstronautFlight
        fields = ('role', 'astronaut')


class SpacecraftStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpacecraftStatus
        fields = ('name',)


class SpacecraftSerializer(serializers.ModelSerializer):
    status = SpacecraftStatusSerializer(read_only=True, many=False)
    spacecraft_config = SpacecraftConfigSerializer(read_only=True, many=False)

    class Meta:
        model = Spacecraft
        fields = ('name', 'serial_number', 'status', 'spacecraft_config')


class SpacecraftFlightSerializer(serializers.ModelSerializer):
    launch_crew = AstronautFlightSerializer(read_only=True, many=True)
    onboard_crew = AstronautFlightSerializer(read_only=True, many=True)
    landing_crew = AstronautFlightSerializer(read_only=True, many=True)
    spacecraft = SpacecraftSerializer(read_only=True, many=False)

    class Meta:
        model = SpacecraftFlight
        fields = ('splashdown', 'launch_crew', 'onboard_crew', 'landing_crew', 'spacecraft')


class RocketSerializer(serializers.ModelSerializer):
    configuration = LauncherConfigSerializer(read_only=True, many=False)
    launcher_stage = FirstStageSerializer(read_only=True, many=True, source='firststage')
    spacecraft_stage = SpacecraftFlightSerializer(read_only=True, many=False, source='spacecraftflight')

    class Meta:
        model = Rocket
        fields = ('configuration', 'launcher_stage', 'spacecraft_stage')


class LaunchSerializer(serializers.HyperlinkedModelSerializer):
    pad = PadSerializer(many=False, read_only=True)
    rocket = RocketSerializer(many=False, read_only=True)
    mission = MissionSerializer(many=False, read_only=True)
    status = LaunchStatusSerializer(many=False, read_only=True)
    slug = serializers.SlugField(source='get_full_absolute_url')

    infoURLs = serializers.ReadOnlyField()
    vidURLs = serializers.ReadOnlyField()

    class Meta:
        depth = 3
        model = Launch
        fields = ('id', 'url', 'launch_library_id', 'slug', 'name', 'img_url', 'status', 'net', 'window_end', 'window_start', 'inhold',
                  'tbdtime', 'tbddate', 'probability', 'holdreason', 'failreason', 'hashtag', 'rocket',
                  'mission', 'pad', 'infoURLs', 'vidURLs')


class EntrySerializer(serializers.ModelSerializer):

    class Meta:
        depth = 3
        model = Entry
        fields = ('id', 'title', 'slug', 'publication_date', 'content', 'lead', 'excerpt', 'image', 'featured',)
