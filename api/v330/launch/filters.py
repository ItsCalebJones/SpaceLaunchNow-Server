from django_filters import filters, FilterSet, ModelChoiceFilter, CharFilter
from django.utils.translation import ugettext as _

from api.models import Launch, Agency


class LaunchFilter(FilterSet):
    net__gt = filters.DateFilter(
        field_name='net', lookup_expr='gt',
        label=_('%s is greater than' % _('NET'))
    )
    net__lt = filters.DateFilter(
        field_name='net', lookup_expr='lt',
        label=_('%s is less than' % _('NET'))
    )
    net__gte = filters.DateFilter(
        field_name='net', lookup_expr='gte',
        label=_('%s is greater than or equal to' % _('NET'))
    )
    net__lte = filters.DateFilter(
        field_name='net', lookup_expr='lte',
        label=_('%s is less than or equal to' % _('NET'))
    )

    rocket__configuration__launch_agency__name = CharFilter(lookup_expr='icontains',
                                                            field_name='rocket__configuration__manufacturer__name')

    class Meta:
        model = Launch
        fields = {
            'name', 'rocket__configuration__name', 'status',
            'launch_library_id', 'rocket__spacecraftflight__spacecraft__name',
            'rocket__spacecraftflight__spacecraft__id',
        }


class LaunchAlternateFilter(FilterSet):

    rocket__configuration__launch_agency__name = CharFilter(lookup_expr='icontains',
                                                            field_name='rocket__configuration__manufacturer__name')

    class Meta:
        model = Launch
        fields = {
            'name', 'rocket__configuration__name', 'status',
            'launch_library_id', 'rocket__spacecraftflight__spacecraft__name',
            'rocket__spacecraftflight__spacecraft__id',
        }
