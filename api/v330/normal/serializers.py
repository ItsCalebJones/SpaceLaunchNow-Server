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
        fields = ('id', 'launch_library_id', 'url', 'name', 'launch_service_provider',)


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
        fields = ('id', 'launch_library_id', 'name', 'description', 'type', 'orbit', 'orbit_abbrev')


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


class SpaceStationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpaceStationStatus
        fields = ('id', 'name', )


class AstronautSerializer(serializers.HyperlinkedModelSerializer):
    status = AstronautStatusSerializer(read_only=True, many=False)
    agency = serializers.StringRelatedField(read_only=True, source='agency.name')

    class Meta:
        model = Astronauts
        fields = ('id', 'url', 'name', 'status', 'agency', 'profile_image')


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
        fields = ('id', 'name',)


class SpacecraftSerializer(serializers.HyperlinkedModelSerializer):
    status = SpacecraftStatusSerializer(read_only=True, many=False)
    configuration = SpacecraftConfigSerializer(read_only=True, many=False, source='spacecraft_config')

    class Meta:
        model = Spacecraft
        fields = ('id', 'url', 'name', 'serial_number', 'status', 'configuration')


class AstronautListSerializer(serializers.HyperlinkedModelSerializer):
    status = AstronautStatusSerializer(read_only=True)
    agency = serializers.ReadOnlyField(read_only=True, source="agency.name")

    class Meta:
        model = Astronauts
        fields = ('id', 'url', 'name', 'status', 'agency', 'nationality', 'profile_image')


class AstronautFlightListSerializer(serializers.ModelSerializer):
    role = serializers.StringRelatedField(read_only=True, source='role.role')
    astronaut = AstronautListSerializer(read_only=True, many=False)

    class Meta:
        model = AstronautFlight
        fields = ('role', 'astronaut')


class AgencyListSerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Agency
        fields = ('id', 'url', 'name', 'abbrev',)


class SpaceStationSerializerForExpedition(serializers.HyperlinkedModelSerializer):
    status = SpaceStationStatusSerializer(read_only=True, many=False)
    owners = AgencyListSerializer(read_only=True, many=True)
    orbit = serializers.StringRelatedField(many=False, read_only=True)

    class Meta:
        model = SpaceStation
        fields = ('id', 'url', 'name', 'status', 'founded', 'description', 'orbit', 'owners',)


class ExpeditionSerializer(serializers.HyperlinkedModelSerializer):
    spacestation = SpaceStationSerializerForExpedition(many=False, read_only=True, source='space_station')

    class Meta:
        model = Expedition
        fields = ('id', 'url', 'name', 'start', 'end', 'spacestation')


class LaunchListSerializer(serializers.ModelSerializer):
    pad = serializers.StringRelatedField()
    location = serializers.StringRelatedField(source='pad.location')
    status = LaunchStatusSerializer(many=False, read_only=True)
    landing = serializers.SerializerMethodField()
    landing_success = serializers.SerializerMethodField()
    launcher = serializers.SerializerMethodField()
    orbit = serializers.SerializerMethodField()
    mission = serializers.StringRelatedField()
    mission_type = serializers.StringRelatedField(source='mission.mission_type.name')
    slug = serializers.SlugField(source='get_full_absolute_url')

    class Meta:
        model = Launch
        fields = (
        'id', 'url', 'launch_library_id', 'slug', 'name', 'status', 'net', 'window_end', 'window_start', 'mission',
        'mission_type',
        'pad', 'location', 'landing', 'landing_success', 'launcher', 'orbit')

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
                cache.set(cache_key, None, CACHE_TIMEOUT_ONE_DAY)
                return None
            elif len(landings) == 1:
                cache.set(cache_key, landings[0].landing_location.abbrev, CACHE_TIMEOUT_ONE_DAY)
                return landings[0].landing_location.abbrev
            elif len(landings) > 1:
                cache.set(cache_key, "MX Landing", CACHE_TIMEOUT_ONE_DAY)
                return "MX Landing"
            else:
                cache.set(cache_key, None, CACHE_TIMEOUT_ONE_DAY)
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
                cache.set(cache_key, None, CACHE_TIMEOUT_ONE_DAY)
                return None
            elif len(landings) == 1:
                landing_status = 0
                if landings[0].success is None:
                    landing_status = 0
                elif landings[0].success:
                    landing_status = 1
                elif not landings[0].success:
                    landing_status = 2
                cache.set(cache_key, landing_status, CACHE_TIMEOUT_ONE_DAY)
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
                cache.set(cache_key, landing_status, CACHE_TIMEOUT_ONE_DAY)
                return landing_status
            else:
                cache.set(cache_key, None, CACHE_TIMEOUT_ONE_DAY)
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


class SpacecraftFlightSerializer(serializers.HyperlinkedModelSerializer):
    spacecraft = SpacecraftSerializer(read_only=True, many=False)
    launch = LaunchListSerializer(read_only=True, many=False, source='rocket.launch')

    class Meta:
        model = SpacecraftFlight
        fields = ('id', 'url', 'destination', 'splashdown', 'spacecraft', 'launch')


class DockingEventSerializer(serializers.ModelSerializer):
    flight_vehicle = SpacecraftFlightSerializer(read_only=True)
    docking_location = serializers.StringRelatedField(many=False, read_only=True)

    class Meta:
        model = DockingEvent
        fields = ('docking', 'departure', 'flight_vehicle', 'docking_location')


class SpaceStationSerializer(serializers.HyperlinkedModelSerializer):
    status = SpaceStationStatusSerializer(read_only=True, many=False)
    owners = AgencyListSerializer(read_only=True, many=True)
    orbit = serializers.StringRelatedField(many=False, read_only=True)

    class Meta:
        model = SpaceStation
        fields = ('id', 'url', 'name', 'status', 'founded', 'description', 'orbit',  'owners',)


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


class AstronautNormalSerializer(serializers.HyperlinkedModelSerializer):
    agency = AgencySerializer(read_only=True, many=False)
    status = AstronautStatusSerializer(read_only=True)

    class Meta:
        model = Astronauts
        fields = ('id', 'url', 'name', 'status', 'date_of_birth', 'date_of_death', 'nationality', 'bio', 'twitter', 'instagram', 'wiki', 'agency', 'profile_image')

