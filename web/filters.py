import django_filters

from api.models import LauncherConfig


class LauncherConfigListFilter(django_filters.FilterSet):
    class Meta:
        model = LauncherConfig
        fields = ['launch_agency', 'family', 'active', 'reusable']
        order_by = ['pk']