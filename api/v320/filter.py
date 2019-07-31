from django_filters import FilterSet, CharFilter

from api.models import LauncherConfig, Launch


class LauncherFilterSet(FilterSet):
    launch_agency__name = CharFilter(lookup_expr='icontains',
                                     name="manufacturer__name")

    class Meta:
        model = LauncherConfig
        fields = ['family', 'name', 'full_name', 'id']


class LaunchFilterSet(FilterSet):
    rocket__configuration__launch_agency__name = CharFilter(lookup_expr='icontains',
                                                            name="rocket__configuration__manufacturer__name")

    class Meta:
        model = Launch
        fields = ['name', 'rocket__configuration__name', 'status',]
