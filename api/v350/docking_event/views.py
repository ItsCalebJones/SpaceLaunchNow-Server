from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend

from api.models import *
from api.permission import HasGroupPermission
from api.v350.docking_event.filters import DockingEventFilter
from api.v350.docking_event.serializers import DockingEventSerializer, DockingEventDetailedSerializer


class DockingEventViewSet(ModelViewSet):
    """
    API endpoint that allows Docking Events to be viewed.

    GET:
    Return a list of all the docking events.

    FILTERS:
    Fields - 'space_station', 'flight_vehicle', 'docking_location'


    MODE:
    'detailed'
    EXAMPLE: ?mode=detailed

    ORDERING:
    Fields - 'id', 'docking', 'departure'
    Order reverse via Docking date.
    Example - /3.3.0/docking_event/?ordering=-docking
    """

    def get_serializer_class(self):
        mode = self.request.query_params.get("mode", "normal")
        if self.action == 'retrieve' or mode == "detailed":
            return DockingEventDetailedSerializer
        else:
            return DockingEventSerializer

    queryset = DockingEvent.objects.all()
    permission_classes = [HasGroupPermission]
    permission_groups = {
        'retrieve': ['_Public'],  # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public']  # list returns None and is therefore NOT accessible by anyone (GET 'site.com/api/foo')
    }
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filter_class = DockingEventFilter
    search_fields = ('space_station__name', 'flight_vehicle__spacecraft__name')
    ordering_fields = ('docking', 'departure',)
