from django_filters import filters, FilterSet
from django.utils.translation import ugettext as _
from api.models import Expedition


class ExpeditionFilter(FilterSet):
    start__gt = filters.DateTimeFilter(
        field_name='start', lookup_expr='gt',
        label=_('%s is greater than' % _('Start'))
    )
    start__lt = filters.DateTimeFilter(
        field_name='start', lookup_expr='lt',
        label=_('%s is less than' % _('Start'))
    )
    start__gte = filters.DateTimeFilter(
        field_name='start', lookup_expr='gt',
        label=_('%s is greater than or equal to' % _('Start'))
    )
    start__lte = filters.DateTimeFilter(
        field_name='start', lookup_expr='lt',
        label=_('%s is greater than or equal to' % _('Start'))
    )
    end__gt = filters.DateTimeFilter(
        field_name='end', lookup_expr='gt',
        label=_('%s is greater than' % _('End'))
    )
    end__lt = filters.DateTimeFilter(
        field_name='end', lookup_expr='lt',
        label=_('%s is less than' % _('End'))
    )
    end__gte = filters.DateTimeFilter(
        field_name='end', lookup_expr='gt',
        label=_('%s is greater than or equal to' % _('End'))
    )
    end__lte = filters.DateTimeFilter(
        field_name='end', lookup_expr='lt',
        label=_('%s is greater than or equal to' % _('End'))
    )

    class Meta:
        model = Expedition
        fields = {
            'name', 'crew__astronaut', 'crew__astronaut__agency', 'space_station'
        }
