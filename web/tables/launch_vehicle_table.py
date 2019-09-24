import django_filters
import django_tables2 as tables
from django.db.models import F
from django_tables2 import SingleTableView, A

from api.models import LauncherConfig


class LaunchVehicleTable(tables.Table):
    name = tables.LinkColumn('launch_vehicle_id', args=[A('pk')])
    total_launch_count = tables.Column(verbose_name='Launch Count')

    class Meta:
        model = LauncherConfig
        fields = ('name', 'family', 'manufacturer', 'maiden_flight', 'active', 'reusable', 'total_launch_count', 'length', 'diameter', 'leo_capacity', 'gto_capacity', 'to_thrust')
        template_name = 'django_tables2/bootstrap4.html'

    def order_leo_capacity(self, QuerySet, is_descending):
        if is_descending:
            QuerySet = QuerySet.order_by(F('leo_capacity').desc(nulls_last=True))
        else:
            QuerySet = QuerySet.order_by(F('leo_capacity').asc(nulls_last=True))
        return (QuerySet, True)

    def order_gto_capacity(self, QuerySet, is_descending):
        if is_descending:
            QuerySet = QuerySet.order_by(F('gto_capacity').desc(nulls_last=True))
        else:
            QuerySet = QuerySet.order_by(F('gto_capacity').asc(nulls_last=True))
        return (QuerySet, True)

    def order_to_thrust(self, QuerySet, is_descending):
        if is_descending:
            QuerySet = QuerySet.order_by(F('to_thrust').desc(nulls_last=True))
        else:
            QuerySet = QuerySet.order_by(F('to_thrust').asc(nulls_last=True))
        return (QuerySet, True)

    def order_length(self, QuerySet, is_descending):
        if is_descending:
            QuerySet = QuerySet.order_by(F('length').desc(nulls_last=True))
        else:
            QuerySet = QuerySet.order_by(F('length').asc(nulls_last=True))
        return (QuerySet, True)

    def order_diameter(self, QuerySet, is_descending):
        if is_descending:
            QuerySet = QuerySet.order_by(F('diameter').desc(nulls_last=True))
        else:
            QuerySet = QuerySet.order_by(F('diameter').asc(nulls_last=True))
        return (QuerySet, True)

    def order_maiden_flight(self, QuerySet, is_descending):
        if is_descending:
            QuerySet = QuerySet.order_by(F('maiden_flight').desc(nulls_last=True))
        else:
            QuerySet = QuerySet.order_by(F('maiden_flight').asc(nulls_last=True))
        return (QuerySet, True)


class LauncherConfigTable(tables.Table):
    name = tables.LinkColumn('launch_vehicle_id', args=[A('pk')])

    class Meta:
        model = LauncherConfig
        fields = ('name', 'family', 'manufacturer', 'maiden_flight', 'active', 'reusable', 'length', 'diameter', 'leo_capacity', 'gto_capacity', 'to_thrust')
        template_name = 'django_tables2/bootstrap4.html'