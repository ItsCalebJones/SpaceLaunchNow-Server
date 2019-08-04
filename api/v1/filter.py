from django_filters import FilterSet, CharFilter

from api.models import LauncherConfig


class LauncherFilterSet(FilterSet):
    launch_agency__name = CharFilter(lookup_expr='icontains', name="manufacturer__name")

    class Meta:
        model = LauncherConfig
        fields = ['family', 'name', 'full_name']