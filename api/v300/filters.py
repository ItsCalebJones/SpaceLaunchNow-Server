import django_filters


class RocketNameFilter(django_filters.FilterSet):
    cities = django_filters.CharFilter(
        name='cities__name',
        lookup_type='contains',
    )

    class Meta:
        model = State
        fields = ('name', 'cities')
