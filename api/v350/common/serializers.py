from drf_queryfields import QueryFieldsMixin
from sorl_thumbnail_serializer.fields import HyperlinkedSorlImageField

from api.models import *
from rest_framework import serializers


class VidURLSerializer(serializers.ModelSerializer):
    url = serializers.URLField(source='vid_url')

    class Meta:
        model = VidURLs
        fields = ('priority', 'title', 'description', 'feature_image', 'url')


class InfoURLSerializer(serializers.ModelSerializer):
    url = serializers.URLField(source='info_url')

    class Meta:
        model = InfoURLs
        fields = ('priority', 'title', 'description', 'feature_image', 'url')


class SpacecraftConfigTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpacecraftConfigurationType
        fields = ('id', 'name',)


class SpaceStationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpaceStationStatus
        fields = ('id', 'name',)


class EventTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventType
        fields = ('id', 'name',)


class SpaceStationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpaceStationStatus
        fields = ('id', 'name',)


class SpacecraftStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpacecraftStatus
        fields = ('id', 'name',)


class AgencyListSerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Agency
        fields = ('id', 'url', 'name', 'abbrev',)


class LaunchStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = LaunchStatus
        fields = ('id', 'name',)


class AstronautStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = AstronautStatus
        fields = ('id', 'name',)


class AstronautTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AstronautType
        fields = ('id', 'name',)


class AgencySerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    parent = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Agency
        fields = ('id', 'url', 'name', 'featured', 'type', 'country_code', 'abbrev', 'description', 'administrator',
                  'founding_year', 'launchers', 'spacecraft', 'parent', 'image_url')


class AgencySerializerMini(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Agency
        fields = ('id', 'url', 'name', 'type')


class AgencySerializerDetailedCommon(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Agency
        fields = ('id', 'url', 'name', 'featured', 'type', 'country_code', 'abbrev', 'description', 'administrator',
                  'founding_year', 'launchers', 'spacecraft', 'launch_library_url', 'total_launch_count',
                  'consecutive_successful_launches', 'successful_launches',
                  'failed_launches', 'pending_launches', 'consecutive_successful_landings',
                  'successful_landings', 'failed_landings', 'attempted_landings', 'info_url', 'wiki_url', 'logo_url',
                  'image_url', 'nation_url',)


class AstronautSerializer(serializers.HyperlinkedModelSerializer):
    status = AstronautStatusSerializer(read_only=True)
    agency = AgencySerializerMini(read_only=True)
    profile_image_thumbnail = HyperlinkedSorlImageField(
        '128x128',
        options={"crop": "80% top"},
        source='profile_image',
        read_only=True
    )

    class Meta:
        model = Astronaut
        fields = ('id', 'url', 'name', 'status', 'agency', 'profile_image', 'profile_image_thumbnail')


class SpacecraftConfigurationDetailSerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    agency = AgencySerializerDetailedCommon(read_only=True, source="manufacturer")
    type = SpacecraftConfigTypeSerializer(read_only=True, many=False)

    class Meta:
        model = SpacecraftConfiguration
        fields = ('id', 'url', 'name', 'type', 'agency', 'in_use', 'capability', 'history', 'details', 'maiden_flight',
                  'height', 'diameter', 'human_rated', 'crew_capacity', 'payload_capacity', 'flight_life',
                  'image_url', 'nation_url', 'wiki_link', 'info_link')


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ('id', 'name', 'country_code', 'map_image', 'total_launch_count', 'total_landing_count')


class PadSerializer(serializers.ModelSerializer):
    location = LocationSerializer(many=False)

    class Meta:
        model = Pad
        fields = ('id', 'agency_id', 'name', 'info_url', 'wiki_url', 'map_url', 'latitude', 'longitude', 'location',
                  'map_image', 'total_launch_count')


class LocationSerializerMini(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ('id', 'name',)


class PadSerializerMini(serializers.ModelSerializer):
    location = LocationSerializerMini(many=False)

    class Meta:
        model = Pad
        fields = ('id', 'name', 'location')


class RocketConfigurationSerializerMini(serializers.ModelSerializer):
    launch_service_provider = AgencySerializerMini(many=False, source='manufacturer')

    class Meta:
        model = LauncherConfig
        fields = ('id', 'url', 'name', 'full_name', 'launch_service_provider', 'image_url')


class RocketSerializerMini(serializers.ModelSerializer):
    configuration = RocketConfigurationSerializerMini(many=False)

    class Meta:
        model = Rocket
        fields = ('id', 'configuration',)


class LandingTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandingType
        fields = ('id', 'name', 'abbrev', 'description',)


class LandingLocationSerializer(serializers.ModelSerializer):
    location = LocationSerializer(many=False)

    class Meta:
        model = LandingLocation
        fields = ('id', 'name', 'abbrev', 'description', 'location', 'successful_landings')


class MissionSerializer(serializers.ModelSerializer):
    type = serializers.StringRelatedField(many=False, source='mission_type')
    orbit = serializers.StringRelatedField(many=False)
    orbit_abbrev = serializers.StringRelatedField(many=False, source='orbit.abbrev')

    class Meta:
        model = Mission
        fields = ('id', 'launch_library_id', 'name', 'description', 'type', 'orbit', 'orbit_abbrev')


class MissionSerializerMini(serializers.ModelSerializer):
    type = serializers.StringRelatedField(many=False, source='mission_type')

    class Meta:
        model = Mission
        fields = ('id', 'launch_library_id', 'name', 'type')


class AstronautDetailedSerializerNoFlights(serializers.HyperlinkedModelSerializer):
    status = AstronautStatusSerializer(read_only=True)
    agency = AgencySerializerMini(read_only=True, many=False)

    class Meta:
        model = Astronaut
        # fields = ('name',)
        fields = ('id', 'url', 'name', 'status', 'agency', 'date_of_birth', 'date_of_death', 'nationality',
                  'twitter', 'instagram', 'bio', 'profile_image', 'wiki', 'last_flight', 'first_flight',)


class AstronautFlightSerializer(serializers.ModelSerializer):
    role = serializers.StringRelatedField(read_only=True, source='role.role')
    astronaut = AstronautDetailedSerializerNoFlights(read_only=True, many=False)

    class Meta:
        model = AstronautFlight
        fields = ('id', 'role', 'astronaut')


class SpacecraftDetailedNoFlightsSerializer(serializers.HyperlinkedModelSerializer):
    status = status = SpacecraftStatusSerializer(read_only=True, many=False)
    spacecraft_config = SpacecraftConfigurationDetailSerializer(read_only=True, many=False)

    class Meta:
        model = Spacecraft
        fields = ('id', 'url', 'name', 'serial_number', 'status', 'description', 'spacecraft_config',)


class DockingLocationSerializer(serializers.ModelSerializer):

    class Meta:
        model = DockingLocation
        fields = ('id', 'name',)


class SpaceStationSerializerForCommon(serializers.HyperlinkedModelSerializer):
    status = SpaceStationStatusSerializer(read_only=True, many=False)
    orbit = serializers.StringRelatedField(many=False, read_only=True)

    class Meta:
        model = SpaceStation
        fields = ('id', 'url', 'name', 'status', 'founded', 'description', 'orbit', 'image_url',)


class DockingLocationSerializer(serializers.ModelSerializer):

    class Meta:
        model = DockingLocation
        fields = ('id', 'name',)


class AstronautFlightForExpeditionSerializer(serializers.ModelSerializer):
    role = serializers.StringRelatedField(read_only=True, source='role.role')
    astronaut = AstronautSerializer(read_only=True, many=False)

    class Meta:
        model = AstronautFlight
        fields = ('id', 'role', 'astronaut')


class DockingEventSerializerForSpacecraftFlight(serializers.ModelSerializer):
    docking_location = DockingLocationSerializer(many=False, read_only=True)
    spacestation = SpaceStationSerializerForCommon(many=False, read_only=True, source='space_station')

    class Meta:
        model = DockingEvent
        fields = ('spacestation', 'docking', 'departure', 'docking_location')


class LauncherConfigListSerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LauncherConfig
        fields = ('id', 'launch_library_id', 'url', 'name', 'family', 'full_name', 'variant',)


class LauncherConfigSerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    manufacturer = AgencySerializer(many=False, read_only=True)

    class Meta:
        model = LauncherConfig
        fields = ('id', 'launch_library_id', 'url', 'name', 'manufacturer', 'family', 'full_name', 'variant',
                  'reusable', 'image_url', 'info_url', 'wiki_url')


class LauncherConfigDetailSerializer(QueryFieldsMixin, serializers.ModelSerializer):
    manufacturer = AgencySerializerDetailedCommon(many=False, read_only=True)

    def get_rep(self, obj):
        rep = obj.rep
        serializer_context = {'request': self.context.get('request'),
                              'id': obj.id}
        serializer = AgencySerializer(rep, context=serializer_context)
        return serializer.data

    class Meta:
        model = LauncherConfig
        fields = ('id', 'launch_library_id', 'url', 'name', 'description', 'family', 'full_name',
                  'manufacturer', 'variant', 'alias', 'min_stage', 'max_stage', 'length', 'diameter',
                  'maiden_flight', 'launch_mass', 'leo_capacity', 'gto_capacity', 'to_thrust', 'apogee',
                  'vehicle_range', 'image_url', 'info_url', 'wiki_url',)


class RocketSerializerCommon(serializers.ModelSerializer):
    configuration = LauncherConfigListSerializer(read_only=True, many=False)

    class Meta:
        model = Rocket
        fields = ('id', 'configuration')


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


class LaunchSerializerCommon(serializers.HyperlinkedModelSerializer):
    pad = PadSerializer(many=False, read_only=True)
    rocket = RocketSerializerCommon(many=False, read_only=True)
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


class SpacecraftConfigSerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    type = SpacecraftConfigTypeSerializer(read_only=True, many=False)
    agency = AgencySerializerMini(read_only=True, source="manufacturer")

    class Meta:
        model = SpacecraftConfiguration
        fields = ('id', 'url', 'name', 'type', 'agency', 'in_use', 'image_url')


class SpacecraftSerializer(serializers.HyperlinkedModelSerializer):
    status = SpacecraftStatusSerializer(read_only=True, many=False)
    configuration = SpacecraftConfigSerializer(read_only=True, many=False, source='spacecraft_config')

    class Meta:
        model = Spacecraft
        fields = ('id', 'url', 'name', 'serial_number', 'status', 'description', 'configuration')


class SpacecraftFlightSerializer(serializers.HyperlinkedModelSerializer):
    spacecraft = SpacecraftSerializer(read_only=True, many=False)
    launch = LaunchSerializerCommon(read_only=True, many=False, source='rocket.launch')

    class Meta:
        model = SpacecraftFlight
        fields = ('id', 'url', 'destination', 'mission_end', 'spacecraft', 'launch')


class SpacecraftFlightDetailedSerializer(serializers.HyperlinkedModelSerializer):
    launch_crew = AstronautFlightSerializer(read_only=True, many=True)
    onboard_crew = AstronautFlightSerializer(read_only=True, many=True)
    landing_crew = AstronautFlightSerializer(read_only=True, many=True)
    spacecraft = SpacecraftDetailedNoFlightsSerializer(read_only=True, many=False)
    docking_events = DockingEventSerializerForSpacecraftFlight(read_only=True, many=True)
    launch = LaunchSerializerCommon(read_only=True, many=False, source='rocket.launch')
    id = serializers.IntegerField(source='pk')

    class Meta:
        model = SpacecraftFlight
        fields = (
            'id', 'url', 'mission_end', 'destination', 'launch_crew', 'onboard_crew', 'landing_crew', 'spacecraft',
            'launch', 'docking_events')

class SpaceStationSerializerForExpedition(serializers.HyperlinkedModelSerializer):
    status = SpaceStationStatusSerializer(read_only=True, many=False)
    orbit = serializers.StringRelatedField(many=False, read_only=True)

    class Meta:
        model = SpaceStation
        fields = ('id', 'url', 'name', 'status', 'orbit', 'image_url',)


class ExpeditionSerializer(serializers.HyperlinkedModelSerializer):
    spacestation = SpaceStationSerializerForExpedition(many=False, read_only=True, source='space_station')

    class Meta:
        model = Expedition
        fields = ('id', 'url', 'name', 'start', 'end', 'spacestation')
