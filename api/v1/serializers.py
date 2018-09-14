from api.models import Orbiter, LauncherConfig, Agency
from rest_framework import serializers


class LauncherModelSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField('get_legacy_name')
    agency = serializers.ReadOnlyField(read_only=True, source="launch_agency.name")

    class Meta:
        model = LauncherConfig
        fields = ('id', 'url', 'name', 'description', 'agency', 'variant', 'image_url', 'info_url', 'wiki_url')

    def get_legacy_name(self, obj):
        if obj.image_url:
            return obj.image_url.url
        else:
            return None


class OrbiterSerializer(serializers.HyperlinkedModelSerializer):
    """
    Space Launch Now public API - for more information join our discord!
    """

    image_url = serializers.SerializerMethodField('get_legacy_name')
    nation_url = serializers.SerializerMethodField('get_nation_name')

    class Meta:
        model = Orbiter
        fields = ('id', 'url', 'name', 'agency', 'history', 'details', 'image_url', 'nation_url',
                  'wiki_link')

    def get_legacy_name(self, obj):
        if obj.image_url:
            return obj.image_url.url
        else:
            return None

    def get_nation_name(self, obj):
        if obj.nation_url:
            return obj.nation_url.url
        else:
            return None


class OrbiterModelSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField('get_legacy_name')
    nation_url = serializers.SerializerMethodField('get_nation_name')

    class Meta:
        model = Orbiter
        fields = ('id', 'url', 'name', 'agency', 'image_url', 'nation_url')

    def get_legacy_name(self, obj):
        if obj.image_url:
            return obj.image_url.url
        else:
            return None

    def get_nation_name(self, obj):
        if obj.nation_url:
            return obj.nation_url.url
        else:
            return None


class AgencySerializer(serializers.HyperlinkedModelSerializer):
    launcher_list = LauncherModelSerializer(many=True, read_only=True)
    orbiter_list = OrbiterModelSerializer(many=True, read_only=True)
    agency = serializers.SerializerMethodField('get_alternate_name')
    image_url = serializers.SerializerMethodField('get_legacy_name')
    nation_url = serializers.SerializerMethodField('get_nation_name')

    class Meta:
        model = Agency
        fields = ('url', 'agency', 'launchers', 'orbiters', 'launcher_list', 'orbiter_list', 'description', 'image_url',
                  'nation_url')

    def get_alternate_name(self, obj):
        return obj.name

    def get_legacy_name(self, obj):
        if obj.image_url:
            return obj.image_url.url
        else:
            return None

    def get_nation_name(self, obj):
        if obj.nation_url:
            return obj.nation_url.url
        else:
            return None


class LauncherDetailSerializer(serializers.HyperlinkedModelSerializer):
    image_url = serializers.SerializerMethodField('get_legacy_name')
    agency = serializers.ReadOnlyField(read_only=True, source="launch_agency.name")

    class Meta:
        model = LauncherConfig
        fields = ('id', 'url', 'name', 'description', 'family', 'full_name', 'agency',
                  'variant', 'alias', 'min_stage', 'max_stage', 'length', 'diameter',
                  'launch_mass', 'leo_capacity', 'gto_capacity', 'to_thrust',
                  'apogee', 'vehicle_range', 'image_url', 'info_url', 'wiki_url')

    def get_legacy_name(self, obj):
        if obj.image_url:
            return obj.image_url.url
        else:
            return None
