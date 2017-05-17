from api.models import Launcher, Orbiter, LauncherDetail
from rest_framework import serializers


class LauncherSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Launcher
        fields = ('id', 'url', 'name', 'agency', 'imageURL', 'nationURL')


class LauncherDetailSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LauncherDetail
        fields = ('id', 'url', 'name', 'agency', 'imageURL', 'nationURL', 'LVInfo')


class OrbiterSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Orbiter
        fields = ('id', 'url', 'name', 'agency', 'history', 'details', 'imageURL', 'nationURL', 'wikiLink')

