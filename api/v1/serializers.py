from api.models import Orbiter, Launcher, Agency
from rest_framework import serializers


class LauncherModelSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField('get_legacy_name')

    class Meta:
        model = Launcher
        fields = ('id', 'url', 'name', 'description', 'agency', 'variant', 'image_url', 'info_url', 'wiki_url')

    def get_legacy_name(self, obj):
        return obj.legacy_image_url


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
        return obj.legacy_image_url

    def get_nation_name(self, obj):
        return obj.legacy_nation_url


class OrbiterModelSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField('get_legacy_name')
    nation_url = serializers.SerializerMethodField('get_nation_name')

    class Meta:
        model = Orbiter
        fields = ('id', 'url', 'name', 'agency', 'image_url', 'nation_url')

    def get_legacy_name(self, obj):
        return obj.legacy_image_url

    def get_nation_name(self, obj):
        return obj.legacy_nation_url


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
        return obj.legacy_image_url

    def get_nation_name(self, obj):
        return obj.legacy_nation_url


class LauncherDetailSerializer(serializers.HyperlinkedModelSerializer):
    image_url = serializers.SerializerMethodField('get_legacy_name')

    class Meta:
        model = Launcher
        fields = ('id', 'url', 'name', 'description', 'family', 'full_name', 'agency',
                  'variant', 'alias', 'min_stage', 'max_stage', 'length', 'diameter',
                  'launch_mass', 'leo_capacity', 'gto_capacity', 'to_thrust', 'vehicle_class',
                  'apogee', 'vehicle_range', 'image_url', 'info_url', 'wiki_url')

    def get_legacy_name(self, obj):
        return obj.legacy_image_url
