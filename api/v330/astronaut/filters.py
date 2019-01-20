from django_filters import filters, FilterSet
from django.utils.translation import ugettext as _
from api.models import Astronaut


class AstronautsFilter(FilterSet):
    date_of_birth__gt = filters.DateFilter(
        field_name='date_of_birth', lookup_expr='gt',
        label=_('%s is greater than' % _('Date of Birth'))
    )
    date_of_birth__lt = filters.DateFilter(
        field_name='date_of_birth', lookup_expr='lt',
        label=_('%s is less than' % _('Date of Birth'))
    )
    date_of_birth__gte = filters.DateFilter(
        field_name='date_of_birth', lookup_expr='gt',
        label=_('%s is greater than or equal to' % _('Date of Birth'))
    )
    date_of_birth__lte = filters.DateFilter(
        field_name='date_of_birth', lookup_expr='lt',
        label=_('%s is greater than or equal to' % _('Date of Birth'))
    )
    date_of_death__gt = filters.DateFilter(
        field_name='date_of_birth', lookup_expr='gt',
        label=_('%s is greater than' % _('Date of Birth'))
    )
    date_of_death__lt = filters.DateFilter(
        field_name='date_of_death', lookup_expr='lt',
        label=_('%s is less than' % _('Date of death'))
    )
    date_of_death__gte = filters.DateFilter(
        field_name='date_of_death', lookup_expr='gt',
        label=_('%s is greater than or equal to' % _('Date of death'))
    )
    date_of_death__lte = filters.DateFilter(
        field_name='date_of_death', lookup_expr='lt',
        label=_('%s is greater than or equal to' % _('Date of death'))
    )

    class Meta:
        model = Astronaut
        fields = {
            'name', 'status', 'nationality', 'agency__name', 'agency__abbrev', 'date_of_birth', 'date_of_death'
        }