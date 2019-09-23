import django_filters

from api.models import LauncherConfig, Launch


class LauncherConfigListFilter(django_filters.FilterSet):
    class Meta:
        model = LauncherConfig
        fields = ['manufacturer', 'family', 'active', 'reusable']
        order_by = ['pk']
