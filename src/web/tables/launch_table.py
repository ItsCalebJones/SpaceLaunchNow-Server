import django_filters
import django_tables2 as tables
from django.db.models import F
from django_tables2 import SingleTableView, A

from api.models import Launch


class LaunchTable(tables.Table):
    name = tables.LinkColumn('launch_by_slug', args=[A('slug')])
    rocket = tables.Column(empty_values=(),
                           verbose_name='Rocket',
                           accessor='rocket.configuration.name')

    class Meta:
        model = Launch
        fields = ('name', 'status', 'launch_service_provider',
                  'rocket', 'mission', 'net', 'pad', )
        template_name = 'django_tables2/bootstrap4.html'
