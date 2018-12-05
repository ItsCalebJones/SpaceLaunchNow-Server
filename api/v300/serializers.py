from rest_framework.relations import HyperlinkedRelatedField

from drf_queryfields import QueryFieldsMixin

from api.models import *
from rest_framework import serializers

from api.utils.custom_serializers import TimeStampField


class AgencySerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    type = serializers.ReadOnlyField(read_only=True, source="agency_type.name")

    class Meta:
        model = Agency
        fields = ('id', 'url', 'name', 'featured', 'launchers', 'orbiters', 'description', 'image_url', 'nation_url',
                  'administrator', 'founding_year', 'logo_url', 'launch_library_url', 'country_code', 'abbrev',
                  'info_url', 'wiki_url', 'type')


class LauncherSerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    agency = serializers.ReadOnlyField(read_only=True, source="launch_agency.name")

    class Meta:
        model = LauncherConfig
        fields = ('id', 'url', 'name', 'agency')


class LauncherDetailSerializer(QueryFieldsMixin, serializers.ModelSerializer):
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


class LauncherDetailSerializerForAgency(QueryFieldsMixin, serializers.ModelSerializer):
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
    agency = serializers.ReadOnlyField(read_only=True, source="launch_agency.name")

    class Meta:
        model = SpacecraftConfiguration
        fields = ('id', 'url', 'name', 'agency', 'history', 'details', 'image_url',
                  'nation_url', 'wiki_link', 'capability')


class AgencyDetailedSerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    launcher_list = LauncherDetailSerializerForAgency(many=True, read_only=True)
    orbiter_list = OrbiterDetailSerializer(many=True, read_only=True)
    type = serializers.ReadOnlyField(read_only=True, source="agency_type.name")

    class Meta:
        model = Agency
        fields = ('id', 'url', 'name', 'featured', 'launchers', 'orbiters', 'description', 'image_url', 'nation_url',
                  'administrator', 'founding_year', 'logo_url', 'launch_library_url', 'country_code', 'abbrev',
                  'launcher_list', 'orbiter_list',)


class OrbiterSerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SpacecraftConfiguration
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
    type = serializers.StringRelatedField(many=False, source='mission_type')

    class Meta:
        model = Agency
        fields = ('id', 'name', 'country_code', 'abbrev', 'type', 'info_url', 'wiki_url')


class MissionSerializer(serializers.ModelSerializer):
    type = serializers.PrimaryKeyRelatedField(read_only=True, many=False, source='mission_type')
    type_name = serializers.StringRelatedField(many=False, source='mission_type')

    class Meta:
        model = Mission
        fields = ('id', 'name', 'description', 'type', 'type_name')


class LaunchListSerializer(serializers.HyperlinkedModelSerializer):
    location = LocationSerializer(many=False, read_only=True, source='pad.location')
    launcher = LauncherSerializer(many=False, read_only=True, source='rocket.configuration')
    lsp = LSPSerializer(many=False, read_only=True, source='rocket.configuration.launch_agency')
    mission = MissionSerializer(many=False, read_only=True)
    status = serializers.IntegerField(
        read_only=True,
        source='status.id'
    )

    class Meta:
        depth = 3
        model = Launch
        fields = ('id', 'url', 'name', 'status', 'net', 'window_end', 'window_start', 'inhold', 'tbdtime', 'tbddate',
                  'launcher', 'mission', 'lsp', 'location')


class LaunchSerializer(serializers.HyperlinkedModelSerializer):
    location = LocationSerializer(many=False, read_only=True, source='pad.location')
    pad = PadSerializer(many=False, read_only=True)
    launcher = LauncherSerializer(many=False, read_only=True, source='rocket.configuration')
    lsp = LSPSerializer(many=False, read_only=True, source='rocket.configuration.launch_agency')
    mission = MissionSerializer(many=False, read_only=True)
    status = serializers.IntegerField(
        read_only=True,
        source='status.id'
    )
    infoURLs = serializers.ReadOnlyField()
    vidURLs = serializers.ReadOnlyField()
    netstamp = TimeStampField(source='net')
    wsstamp = TimeStampField(source='window_start')
    westamp = TimeStampField(source='window_end')
    isonet = serializers.DateTimeField(format="%Y%m%dT%H%M%SZ", input_formats=None, source='net')
    isostart = serializers.DateTimeField(format="%Y%m%dT%H%M%SZ", input_formats=None, source='window_start')
    isoend = serializers.DateTimeField(format="%Y%m%dT%H%M%SZ", input_formats=None, source='window_end')

    class Meta:
        depth = 3
        model = Launch
        fields = ('id', 'url', 'name', 'img_url', 'status', 'netstamp', 'wsstamp', 'westamp', 'net', 'window_end',
                  'window_start', 'isonet', 'isostart', 'isoend', 'inhold', 'tbdtime', 'tbddate', 'probability',
                  'holdreason', 'failreason', 'hashtag', 'launcher', 'mission', 'lsp', 'location', 'pad', 'infoURLs',
                  'vidURLs')


class InfoURLSerializer(serializers.ModelSerializer):
    class Meta:
        model = InfoURLs
        fields = ('info_url',)


class LaunchDetailedSerializer(serializers.HyperlinkedModelSerializer):
    location = LocationSerializer(many=False, read_only=True, source='pad.location')
    pad = PadSerializer(many=False, read_only=True)
    launcher = LauncherDetailSerializerForAgency(many=False, read_only=True, source='rocket.configuration')
    lsp = AgencySerializer(many=False, read_only=True, source='rocket.configuration.launch_agency')
    mission = MissionSerializer(many=False, read_only=True)
    infoURLs = serializers.StringRelatedField(read_only=True, many=True, source='info_urls')
    vidURLs = serializers.StringRelatedField(read_only=True, many=True, source='vid_urls')
    status = serializers.IntegerField(
        read_only=True,
        source='status.id'
    )
    netstamp = TimeStampField(source='net')
    wsstamp = TimeStampField(source='window_start')
    westamp = TimeStampField(source='window_end')
    isonet = serializers.DateTimeField(format="%Y%m%dT%H%M%SZ", input_formats=None, source='net')
    isostart = serializers.DateTimeField(format="%Y%m%dT%H%M%SZ", input_formats=None, source='window_start')
    isoend = serializers.DateTimeField(format="%Y%m%dT%H%M%SZ", input_formats=None, source='window_end')

    class Meta:
        depth = 3
        model = Launch
        fields = ('id', 'url', 'name', 'img_url', 'status', 'netstamp', 'wsstamp', 'westamp', 'net', 'window_end',
                  'window_start', 'isonet', 'isostart', 'isoend', 'inhold', 'tbdtime', 'tbddate', 'probability',
                  'holdreason', 'failreason', 'hashtag', 'launcher', 'mission', 'lsp', 'location', 'pad', 'infoURLs',
                  'vidURLs')
