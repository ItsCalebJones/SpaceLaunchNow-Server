from drf_queryfields import QueryFieldsMixin
from zinnia.models import Entry

from api.models import *
from rest_framework import serializers


class AgencySerializerMini(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Agency
        fields = ('id', 'url', 'name', 'description', 'related_agencies', 'administrator', 'founding_year', 'type')

    def get_fields(self):
        fields = super(AgencySerializerMini, self).get_fields()
        fields['related_agencies'] = AgencySerializerMini(many=True)
        return fields


class AgencySerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    parent = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Agency
        fields = ('id', 'url', 'name', 'featured', 'type', 'country_code', 'abbrev', 'description', 'administrator',
                  'founding_year', 'launchers', 'orbiters', 'parent', 'related_agencies',)

    def get_fields(self):
        fields = super(AgencySerializer, self).get_fields()
        fields['related_agencies'] = AgencySerializerMini(many=True)
        return fields


class AgencySerializerDetailed(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    parent = serializers.StringRelatedField(read_only=True)

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


class LauncherSerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Launcher
        fields = ('id', 'url', 'serial_number', 'previous_flights')


class LauncherDetailedSerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Launcher
        fields = ('id', 'url', 'serial_number', 'previous_flights')


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
                  'variant', 'alias', 'min_stage', 'max_stage', 'length', 'diameter',
                  'launch_mass', 'leo_capacity', 'gto_capacity', 'to_thrust',
                  'apogee', 'vehicle_range', 'image_url', 'info_url', 'wiki_url',)


class OrbiterDetailSerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Orbiter
        fields = ('id', 'url', 'name', 'agency', 'history', 'details', 'image_url', 'nation_url', 'wiki_link', 'capability')


class AgencyDetailedSerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    launcher_list = LauncherConfigDetailSerializerForAgency(many=True, read_only=True)
    orbiter_list = OrbiterDetailSerializer(many=True, read_only=True)

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
        model = Orbiter
        fields = ('id', 'url', 'name')


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


class LocationSerializer(serializers.ModelSerializer):
    pads = PadSerializer(many=True, read_only=True)

    class Meta:
        model = Location
        fields = ('id', 'name', 'country_code', 'pads')


class LSPSerializer(serializers.ModelSerializer):
    parent = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Agency
        fields = ('id', 'name', 'parent', 'country_code', 'abbrev', 'type', 'info_url', 'wiki_url')


class MissionSerializer(serializers.ModelSerializer):
    mission_type = serializers.StringRelatedField(many=False)

    class Meta:
        model = Mission
        fields = ('id', 'name', 'description', 'mission_type')


class LaunchListSerializer(serializers.HyperlinkedModelSerializer):
    location = LocationSerializer(many=False, read_only=True, source='pad.location')
    launcher_config = LauncherConfigSerializer(many=False, read_only=True)
    lsp = LSPSerializer(many=False, read_only=True)
    mission = MissionSerializer(many=False, read_only=True)

    class Meta:
        depth = 3
        model = Launch
        fields = ('id', 'url', 'name', 'status', 'net', 'window_end', 'window_start', 'inhold', 'tbdtime', 'tbddate',
                  'launcher_config', 'mission', 'lsp', 'location')


class LaunchSerializer(serializers.HyperlinkedModelSerializer):
    location = LocationSerializer(many=False, read_only=True, source='pad.location')
    pad = PadSerializer(many=False, read_only=True)
    launcher_config = LauncherConfigSerializer(many=False, read_only=True)
    lsp = LSPSerializer(many=False, read_only=True)
    mission = MissionSerializer(many=False, read_only=True)

    infoURLs = serializers.ReadOnlyField()
    vidURLs = serializers.ReadOnlyField()

    class Meta:
        depth = 3
        model = Launch
        fields = ('id', 'url', 'name', 'img_url', 'status', 'net', 'window_end', 'window_start', 'inhold', 'tbdtime',
                  'tbddate', 'probability', 'holdreason', 'failreason', 'hashtag', 'launcher_config', 'mission',
                  'lsp', 'location', 'pad', 'infoURLs', 'vidURLs')


class LaunchDetailedSerializer(serializers.HyperlinkedModelSerializer):
    location = LocationSerializer(many=False, read_only=True, source='pad.location')
    pad = PadSerializer(many=False, read_only=True)
    launcher_config = LauncherConfigDetailSerializerForAgency(many=False, read_only=True)
    launcher = LauncherSerializer(many=False, read_only=True)
    lsp = AgencySerializerDetailed(many=False, read_only=True)
    mission = MissionSerializer(many=False, read_only=True)

    infoURLs = serializers.ReadOnlyField()
    vidURLs = serializers.ReadOnlyField()

    class Meta:
        depth = 3
        model = Launch
        fields = ('id', 'url', 'name', 'img_url', 'status', 'net', 'window_end', 'window_start', 'inhold', 'tbdtime',
                  'tbddate', 'probability', 'holdreason', 'failreason', 'reused', 'land_success', 'landing_type',
                  'landing_location', 'hashtag', 'launcher', 'launcher_config', 'mission', 'lsp', 'location', 'pad',
                  'infoURLs', 'vidURLs')


class EntrySerializer(serializers.ModelSerializer):

    class Meta:
        depth = 3
        model = Entry
        fields = ('id', 'title', 'slug', 'publication_date', 'content', 'lead', 'excerpt', 'image', 'featured',)
