from api.models import Launcher, Orbiter, LauncherDetail
from rest_framework import serializers


class LauncherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Launcher
        fields = ('id', 'name', 'agency', 'imageURL', 'nationURL')


class LauncherDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = LauncherDetail
        fields = ('id', 'name', 'agency', 'imageURL', 'nationURL', 'LVInfo')


class OrbiterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Orbiter
        fields = ('id', 'name', 'agency', 'history', 'details', 'imageURL', 'nationURL', 'wikiLink')

