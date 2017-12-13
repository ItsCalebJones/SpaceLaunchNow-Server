from api.models import Launcher, Orbiter, LauncherDetail
from rest_framework import serializers


class LauncherSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Launcher
        fields = ('id', 'url', 'name', 'agency', 'image_url', 'nation_url')


class OrbiterSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Orbiter
        fields = ('id', 'url', 'name', 'agency', 'history', 'details', 'image_url', 'nation_url',
                  'wiki_link')


class LauncherDetailSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LauncherDetail
        fields = ('id', 'url', 'name', 'description', 'family', 's_family', 'agency',
                  'variant', 'alias', 'min_stage', 'max_stage', 'length', 'diameter',
                  'launch_mass', 'leo_capacity', 'gto_capacity', 'to_thrust', 'vehicle_class',
                  'apogee', 'vehicle_range', 'image_url', 'info_url', 'wiki_url')

