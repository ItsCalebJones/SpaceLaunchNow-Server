import django_filters
from django.db.models import Q
from django.forms.widgets import CheckboxSelectMultiple

from api.models import LauncherConfig, Launch, Location, Pad


class LaunchListFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(field_name='search', label="Search", method='filter_by_all_name_fields')
    location = django_filters.ModelChoiceFilter(field_name='pad__location',
                                                queryset=Location.objects.all(),
                                                label="Location")
    start_date = django_filters.DateFilter(field_name='net', lookup_expr='gte', label="Start Date")
    end_date = django_filters.DateFilter(field_name='net', lookup_expr='lte', label="End Date")

    class Meta:
        model = Launch
        fields = ['search', 'launch_service_provider', 'status', 'location', 'start_date', 'end_date']
        order_by = ['-net']

    def filter_by_all_name_fields(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(mission__name__icontains=value) |
            Q(rocket__configuration__full_name__icontains=value) |
            Q(rocket__configuration__name__icontains=value) |
            Q(launch_service_provider__name__icontains=value) |
            Q(launch_service_provider__abbrev__icontains=value)
        )
