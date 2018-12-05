from drf_queryfields import QueryFieldsMixin
from zinnia.models import Entry

from api.models import *
from rest_framework import serializers


class AgencySerializerMini(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    parent = serializers.StringRelatedField(read_only=True)
    type = serializers.ReadOnlyField(read_only=True, source="agency_type.name")

    class Meta:
        model = Agency
        fields = ('id', 'url', 'name', 'description', 'parent', 'related_agencies', 'administrator', 'founding_year', 'type')


class AgencySerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    parent = serializers.StringRelatedField(read_only=True)
    type = serializers.ReadOnlyField(read_only=True, source="agency_type.name")

    class Meta:
        model = Agency
        fields = ('id', 'url', 'name', 'featured', 'type', 'country_code', 'abbrev', 'description', 'administrator',
                  'founding_year', 'launchers', 'orbiters', 'parent', 'related_agencies',)


class AgencySerializerDetailed(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    parent = serializers.StringRelatedField(read_only=True)
    type = serializers.ReadOnlyField(read_only=True, source="agency_type.name")

    class Meta:
        model = Agency
        fields = ('id', 'url', 'name', 'featured', 'type', 'country_code', 'abbrev', 'description', 'administrator',
                  'founding_year', 'launchers', 'orbiters', 'parent', 'launch_library_url', 'successful_launches',
                  'failed_launches', 'pending_launches', 'info_url', 'wiki_url', 'logo_url', 'image_url', 'nation_url',
                  'related_agencies',)

    def get_fields(self):
        fields = super(AgencySerializerDetailed, self).get_fields()
        fields['related_agencies'] = AgencySerializerDetailed(many=True)
        return fields


class LauncherSerializer(QueryFieldsMixin, serializers.ModelSerializer):

    class Meta:
        model = Launcher
        fields = ('id', 'url', 'flight_proven', 'serial_number')


class LauncherDetailedSerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Launcher
        fields = ('id', 'url', 'flight_proven', 'serial_number', 'status', 'previous_flights')


class LauncherConfigSerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    agency = serializers.ReadOnlyField(read_only=True, source="launch_agency.name")

    class Meta:
        model = LauncherConfig
        fields = ('id', 'url', 'name', 'agency')


class LauncherConfigDetailSerializer(QueryFieldsMixin, serializers.ModelSerializer):
    agency = AgencySerializer(many=False, read_only=True, source='launch_agency')

    def get_rep(self, obj):
        rep = obj.rep
        serializer_context = {'request': self.context.get('request'),
                              'id': obj.id}
        serializer = AgencySerializer(rep, context=serializer_context)
        return serializer.data

    class Meta:
        model = LauncherConfig
        fields = ('id', 'url', 'name', 'description', 'family', 'full_name', 'agency',
                  'variant', 'alias', 'min_stage', 'max_stage', 'length', 'diameter',
                  'launch_mass', 'leo_capacity', 'gto_capacity', 'to_thrust',
                  'apogee', 'vehicle_range', 'image_url', 'info_url', 'wiki_url',)


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
                  'variant', 'alias', 'min_stage', 'max_stage', 'length', 'diameter', 'launch_cost',
                  'launch_mass', 'leo_capacity', 'gto_capacity', 'geo_capacity', 'sso_capacity', 'to_thrust',
                  'apogee', 'vehicle_range', 'image_url', 'info_url', 'wiki_url',)


class OrbiterDetailSerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    agency = serializers.ReadOnlyField(read_only=True, source="launch_agency.name")

    class Meta:
        model = SpacecraftConfiguration
        fields = ('id', 'url', 'name', 'agency', 'in_use', 'capability', 'history', 'details', 'maiden_flight',
                  'height', 'diameter', 'human_rated', 'crew_capacity', 'payload_capacity', 'flight_life',
                  'image_url', 'nation_url', 'wiki_link', 'info_link')


class AgencyDetailedSerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    launcher_list = LauncherConfigDetailSerializerForAgency(many=True, read_only=True)
    orbiter_list = OrbiterDetailSerializer(many=True, read_only=True)
    type = serializers.ReadOnlyField(read_only=True, source="agency_type.name")
    parent = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Agency
        fields = ('id', 'url', 'name', 'featured', 'type', 'country_code', 'abbrev', 'description', 'administrator',
                  'founding_year', 'launchers', 'orbiters', 'parent', 'launch_library_url', 'successful_launches',
                  'failed_launches', 'pending_launches', 'info_url', 'wiki_url', 'logo_url', 'image_url', 'nation_url',
                  'launcher_list', 'orbiter_list', 'related_agencies',)

    def get_fields(self):
        fields = super(AgencyDetailedSerializer, self).get_fields()
        fields['related_agencies'] = AgencySerializerDetailed(many=True)
        return fields


class OrbiterSerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SpacecraftConfiguration
        fields = ('id', 'url', 'name', 'in_use')


class EventsSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Events
        fields = ('id', 'url', 'name', 'description', 'location', 'feature_image', 'date')


# class RocketSerializer(serializers.ModelSerializer):
#
#     class Meta:
#         model = Rocket
#         fields = ('id', 'name', 'imageURL', 'family_name')


class PadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pad
        fields = ('id', 'agency_id', 'name', 'info_url', 'wiki_url', 'map_url', 'latitude', 'longitude')


class LaunchStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = LaunchStatus
        fields = ('id', 'name',)


class LocationSerializer(serializers.ModelSerializer):
    pads = PadSerializer(many=True, read_only=True)

    class Meta:
        model = Location
        fields = ('id', 'name', 'country_code', 'pads')


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


class LaunchListSerializer(serializers.HyperlinkedModelSerializer):
    location = LocationSerializer(many=False, read_only=True, source='pad.location')
    lsp = LSPSerializer(many=False, read_only=True, source='rocket.configuration.launch_agency')
    status = LaunchStatusSerializer(many=False, read_only=True)
    slug = serializers.SlugField(source='get_full_absolute_url')
    
    class Meta:
        depth = 3
        model = Launch
        fields = ('id', 'url', 'slug', 'name', 'status', 'net', 'window_end', 'window_start', 'inhold', 'tbdtime', 'tbddate',
                  'lsp', 'location')


class LaunchSerializer(serializers.HyperlinkedModelSerializer):
    location = LocationSerializer(many=False, read_only=True, source='pad.location')
    pad = PadSerializer(many=False, read_only=True)
    launcher_config = LauncherConfigSerializer(many=False, read_only=True, source='rocket.configuration')
    lsp = LSPSerializer(many=False, read_only=True, source='rocket.configuration.launch_agency')
    mission = MissionSerializer(many=False, read_only=True)
    status = LaunchStatusSerializer(many=False, read_only=True)
    slug = serializers.SlugField(source='get_full_absolute_url')

    infoURLs = serializers.ReadOnlyField()
    vidURLs = serializers.ReadOnlyField()

    class Meta:
        depth = 3
        model = Launch
        fields = ('id', 'url', 'slug', 'name', 'img_url', 'status', 'net', 'window_end', 'window_start', 'inhold', 'tbdtime',
                  'tbddate', 'probability', 'holdreason', 'failreason', 'hashtag', 'launcher_config',
                  'mission', 'lsp', 'location', 'pad', 'infoURLs', 'vidURLs')


class LaunchDetailedSerializer(serializers.HyperlinkedModelSerializer):
    location = LocationSerializer(many=False, read_only=True, source='pad.location')
    pad = PadSerializer(many=False, read_only=True)
    launcher_config = LauncherConfigDetailSerializerForAgency(many=False, read_only=True, source='rocket.configuration')
    lsp = AgencySerializerDetailed(many=False, read_only=True, source='rocket.configuration.launch_agency')
    mission = MissionSerializer(many=False, read_only=True)
    status = LaunchStatusSerializer(many=False, read_only=True)
    slug = serializers.SlugField(source='get_full_absolute_url')

    infoURLs = serializers.StringRelatedField(read_only=True, many=True, source='info_urls')
    vidURLs = serializers.StringRelatedField(read_only=True, many=True, source='vid_urls')

    class Meta:
        depth = 3
        model = Launch
        fields = ('id', 'url', 'slug', 'name', 'img_url', 'status', 'net', 'window_end', 'window_start', 'inhold',
                  'tbdtime', 'tbddate', 'probability', 'holdreason', 'failreason', 'hashtag',
                  'launcher_config', 'mission', 'lsp', 'location', 'pad', 'infoURLs', 'vidURLs')


class EntrySerializer(serializers.ModelSerializer):

    class Meta:
        depth = 3
        model = Entry
        fields = ('id', 'title', 'slug', 'publication_date', 'content', 'lead', 'excerpt', 'image', 'featured',)
