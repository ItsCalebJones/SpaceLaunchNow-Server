from django_filters import FilterSet, CharFilter, ModelChoiceFilter

from api.models import LauncherConfig, Launcher, Agency, SpacecraftConfiguration


class LauncherFilterSet(FilterSet):
    launcher_config__launch_agency = ModelChoiceFilter(queryset=Agency.objects.all())

    class Meta:
        model = Launcher
        fields = ['id', 'serial_number', 'flight_proven', 'launcher_config']


class SpacecraftConfigFilterSet(FilterSet):
    launch_agency = ModelChoiceFilter(queryset=Agency.objects.all())

    class Meta:
        model = SpacecraftConfiguration
        fields = ['name', 'in_use', 'human_rated']


class LauncherConfigFilterSet(FilterSet):
    launch_agency = ModelChoiceFilter(queryset=Agency.objects.all())

    class Meta:
        model = LauncherConfig
        fields = ['family', 'name', 'full_name', 'active', 'reusable']