from api.models import Orbiter, Launcher, Agency, Events
from drf_queryfields import QueryFieldsMixin

from api.models import Orbiter, Launcher, Agency
from rest_framework import serializers


class LauncherModelSerializer(QueryFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Launcher
        fields = ('id', 'url', 'name', 'description', 'agency', 'variant',  'image_url',
                  'info_url', 'wiki_url')


class OrbiterSerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Orbiter
        fields = ('id', 'url', 'name', 'agency', 'history', 'details', 'image_url',
                  'legacy_nation_url', 'nation_url', 'wiki_link', 'in_use', 'capability')


class OrbiterModelSerializer(QueryFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Orbiter
        fields = ('id', 'url', 'name', 'agency', 'image_url', 'legacy_nation_url', 'nation_url')


class AgencyHyperlinkedSerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    launcher_list = LauncherModelSerializer(many=True, read_only=True)
    orbiter_list = OrbiterModelSerializer(many=True, read_only=True)

    ceo = serializers.SerializerMethodField('get_administrator')

    class Meta:
        model = Agency
        fields = ('id', 'url', 'name', 'featured', 'launchers', 'orbiters', 'launcher_list', 'orbiter_list',
                  'description', 'legacy_image_url', 'image_url', 'legacy_nation_url', 'nation_url', 'ceo',
                  'founding_year', 'logo_url', 'launch_library_url',)

    @staticmethod
    def get_administrator(obj):
        return obj.administrator


# class AgencyModelSerializer(QueryFieldsMixin, serializers.ModelSerializer):
#     launcher_list = LauncherModelSerializer(many=True, read_only=True)
#     orbiter_list = OrbiterModelSerializer(many=True, read_only=True)
#
#     class Meta:
#         model = Agency
#         fields = ('id', 'url', 'name', 'featured', 'launchers', 'orbiters', 'launcher_list', 'orbiter_list',
#                   'description', 'legacy_image_url', 'image_url', 'legacy_nation_url', 'nation_url', 'ceo',
#                   'founding_year', 'logo_url', 'launch_library_url', 'launch_library_id')


class LauncherDetailSerializer(QueryFieldsMixin, serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Launcher
        fields = ('id', 'url', 'name', 'description', 'family', 'full_name', 'agency',
                  'variant', 'alias', 'min_stage', 'max_stage', 'length', 'diameter',
                  'launch_mass', 'leo_capacity', 'gto_capacity', 'to_thrust',
                  'apogee', 'vehicle_range', 'image_url', 'info_url', 'wiki_url')


class EventsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Events
        fields = ('id', 'name', 'description', 'location', 'feature_image', 'date')
