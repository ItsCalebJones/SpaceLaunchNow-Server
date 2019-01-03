from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from api.models import *
from api.permission import HasGroupPermission
from api.v330.common.serializers import SpacecraftFlightDetailedSerializer, SpacecraftFlightSerializer


class SpaceflightFlightViewSet(ModelViewSet):
    """
    API endpoint that allows a flight of a specific Spacecraft instances to be viewed.

    GET:
    Return a list of all the existing Spacecraft flights.

    FILTERS:
    Parameters - 'spacecraft'
    Example - /api/3.3.0/launcher/?spacecraft=37
    """
    def get_serializer_class(self):
        mode = self.request.query_params.get("mode", "normal")
        if self.action == 'retrieve' or mode == "detailed":
            return SpacecraftFlightDetailedSerializer
        else:
            return SpacecraftFlightSerializer

    queryset = SpacecraftFlight.objects.all()
    permission_classes = [HasGroupPermission]
    permission_groups = {
        'retrieve': ['_Public'], # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public'] # list returns None and is therefore NOT accessible by anyone (GET 'site.com/api/foo')
    }
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('spacecraft',)
