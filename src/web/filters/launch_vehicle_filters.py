import django_filters
from api.models import LauncherConfig
from django.db.models import Q


class LauncherConfigListFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(field_name="search", label="Search", method="filter_by_all_name_fields")

    class Meta:
        model = LauncherConfig
        fields = ["manufacturer", "family", "active", "reusable"]
        order_by = ["pk"]

    def filter_by_all_name_fields(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value)
            | Q(description__icontains=value)
            | Q(full_name__icontains=value)
            | Q(variant__icontains=value)
            | Q(alias__icontains=value)
            | Q(manufacturer__name__icontains=value)
            | Q(manufacturer__abbrev__icontains=value)
        )
