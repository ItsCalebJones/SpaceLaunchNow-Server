from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from api.models import *
from api.permission import HasGroupPermission
from api.v350.spacestation.serializers import SpaceStationDetailedSerializer, SpaceStationSerializer


class SpaceStationViewSet(ModelViewSet):
    """
    API endpoint that allows Space Stations to be viewed.

    GET:
    Return a list of all the existing space stations.

    FILTERS:
    Parameters - 'name', 'status', 'owners', 'orbit', 'type', 'owners__name', 'owners__abrev'
    Example - /api/3.3.0/spacestation/?status=Active

    SEARCH EXAMPLE:
    Example - /api/3.3.0/spacestation/?search=ISS
    Searches through 'name', 'owners__name', 'owners__abbrev'

    ORDERING:
    Fields - 'id', 'status', 'type', 'founded', 'volume'
    Example - /api/3.3.0/spacestation/?ordering=id
    """

    def get_serializer_class(self):
        mode = self.request.query_params.get("mode", "normal")
        if self.action == 'retrieve' or mode == "detailed":
            return SpaceStationDetailedSerializer
        else:
            return SpaceStationSerializer

    queryset = SpaceStation.objects.all()
    permission_classes = [HasGroupPermission]
    permission_groups = {
        'retrieve': ['_Public'], # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public'] # list returns None and is therefore NOT accessible by anyone (GET 'site.com/api/foo')
    }
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filter_fields = ('name', 'status', 'owners', 'orbit', 'type', 'owners__name', 'owners__abbrev')
    search_fields = ('$name', 'owners__name', 'owners__abbrev')
    ordering_fields = ('id', 'status', 'type', 'founded', 'volume')