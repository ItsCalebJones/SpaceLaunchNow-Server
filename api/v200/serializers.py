from api.models import Orbiter, LauncherDetail, Agency
from rest_framework import serializers


class LauncherModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = LauncherDetail
        fields = ('id', 'url', 'name', 'description', 'agency', 'variant', 'image_url', 'info_url', 'wiki_url')


class OrbiterSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Orbiter
        fields = ('id', 'url', 'name', 'agency', 'history', 'details', 'image_url', 'nation_url',
                  'wiki_link')


class OrbiterModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Orbiter
        fields = ('id', 'url', 'name', 'agency', 'image_url', 'nation_url')


class AgencySerializer(serializers.HyperlinkedModelSerializer):
    launcher_list = LauncherModelSerializer(many=True, read_only=True)
    orbiter_list = OrbiterModelSerializer(many=True, read_only=True)

    class Meta:
        model = Agency
        fields = ('url', 'name', 'launchers', 'orbiters', 'launcher_list', 'orbiter_list', 'description', 'image_url',
                  'nation_url', 'ceo', 'founding_year', 'logo_url', 'launch_library_url', 'launch_library_id',
                  'featured')


class LauncherDetailSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LauncherDetail
        fields = ('id', 'url', 'name', 'description', 'family', 's_family', 'full_name', 'agency',
                  'variant', 'alias', 'min_stage', 'max_stage', 'length', 'diameter',
                  'launch_mass', 'leo_capacity', 'gto_capacity', 'to_thrust', 'vehicle_class',
                  'apogee', 'vehicle_range', 'image_url', 'info_url', 'wiki_url')

