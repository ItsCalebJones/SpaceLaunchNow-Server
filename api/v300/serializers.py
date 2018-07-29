from rest_framework.relations import HyperlinkedRelatedField

from drf_queryfields import QueryFieldsMixin

from api.models import *
from rest_framework import serializers


class AgencySerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Agency
        fields = ('id', 'url', 'name', 'featured', 'launchers', 'orbiters', 'description', 'image_url', 'nation_url',
                  'administrator', 'founding_year', 'logo_url', 'launch_library_url', 'country_code', 'abbrev',
                  'info_url', 'wiki_url', 'type')


class LauncherSerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    agency = serializers.ReadOnlyField(read_only=True, source="launch_agency.name")

    class Meta:
        model = Launcher
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
        model = Launcher
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
        model = Launcher
        fields = ('id', 'url', 'name', 'description', 'family', 'full_name',
                  'variant', 'alias', 'min_stage', 'max_stage', 'length', 'diameter',
                  'launch_mass', 'leo_capacity', 'gto_capacity', 'to_thrust',
                  'apogee', 'vehicle_range', 'image_url', 'info_url', 'wiki_url',)


class OrbiterDetailSerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Orbiter
        fields = ('id', 'url', 'name', 'agency', 'history', 'details', 'image_url',
                  'legacy_nation_url', 'nation_url', 'wiki_link', 'capability')


class AgencyDetailedSerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    launcher_list = LauncherDetailSerializerForAgency(many=True, read_only=True)
    orbiter_list = OrbiterDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Agency
        fields = ('id', 'url', 'name', 'featured', 'launchers', 'orbiters', 'description', 'image_url', 'nation_url',
                  'administrator', 'founding_year', 'logo_url', 'launch_library_url', 'country_code', 'abbrev',
                  'launcher_list', 'orbiter_list',)


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

    class Meta:
        model = Agency
        fields = ('id', 'name', 'country_code', 'abbrev', 'type', 'info_url', 'wiki_url')


class MissionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Mission
        fields = ('id', 'name', 'description', 'type', 'type_name')


class LaunchSerializer(serializers.HyperlinkedModelSerializer):
    location = LocationSerializer(many=False, read_only=True, source='pad.location')
    pad = PadSerializer(many=False, read_only=True)
    launcher = LauncherDetailSerializer(many=False, read_only=True)
    lsp = LSPSerializer(many=False, read_only=True)
    mission = MissionSerializer(many=False, read_only=True)

    infoURLs = serializers.ReadOnlyField()
    vidURLs = serializers.ReadOnlyField()

    class Meta:
        depth = 3
        model = Launch
        fields = ('id', 'url', 'name', 'img_url', 'status', 'netstamp', 'wsstamp', 'westamp', 'net', 'window_end',
                  'window_start', 'isonet', 'isostart', 'isoend', 'inhold', 'tbdtime', 'tbddate', 'probability',
                  'holdreason', 'failreason', 'hashtag', 'launcher', 'mission', 'lsp', 'location', 'pad', 'infoURLs',
                  'vidURLs')



