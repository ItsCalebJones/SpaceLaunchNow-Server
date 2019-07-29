from django_filters import FilterSet, filters
from django.utils.translation import ugettext as _

from api.models import DockingEvent


class DockingEventFilter(FilterSet):
    docking__gt = filters.DateTimeFilter(
        field_name='docking', lookup_expr='gt',
        label=_('%s is greater than' % _('Docking'))
    )
    docking__lt = filters.DateTimeFilter(
        field_name='docking', lookup_expr='lt',
        label=_('%s is less than' % _('Docking'))
    )
    docking__gte = filters.DateTimeFilter(
        field_name='docking', lookup_expr='gte',
        label=_('%s is greater than or equal to' % _('Docking'))
    )
    docking__lte = filters.DateTimeFilter(
        field_name='docking', lookup_expr='lte',
        label=_('%s is less than or equal to' % _('Docking'))
    )

    class Meta:
        model = DockingEvent
        fields = (
            'space_station', 'flight_vehicle', 'docking_location',
        )