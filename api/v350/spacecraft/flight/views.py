from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from api.models import *
from api.permission import HasGroupPermission
from api.v350.common.serializers import SpacecraftFlightDetailedSerializer, SpacecraftFlightSerializer


class SpaceflightFlightViewSet(ModelViewSet):
    """
    API endpoint that allows a flight of a specific Spacecraft instances to be viewed.

    GET:
    Return a list of all the existing Spacecraft flights.

    FILTERS:
    Parameters - 'spacecraft'
    Example - /api/3.5.0/launcher/?spacecraft=37
    """
    def get_serializer_class(self):
        mode = self.request.query_params.get("mode", "normal")
        if self.action == 'retrieve' or mode == "detailed":
            return SpacecraftFlightDetailedSerializer
        else:
            return SpacecraftFlightSerializer

    queryset = SpacecraftFlight.objects.all().prefetch_related(
        'spacecraft__spacecraft_config__type').prefetch_related(
        'spacecraft__status').prefetch_related(
        'spacecraft__spacecraft_config__manufacturer').prefetch_related(
        'rocket__configuration__manufacturer').prefetch_related(
        'rocket__launch__mission').prefetch_related(
        'rocket__launch').prefetch_related(
        'rocket').prefetch_related(
        'rocket__launch__status').prefetch_related(
        'rocket__configuration__manufacturer').prefetch_related(
        'spacecraft__spacecraft_config__manufacturer').select_related('rocket__launch')
    permission_classes = [HasGroupPermission]
    permission_groups = {
        'retrieve': ['_Public'], # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public'] # list returns None and is therefore NOT accessible by anyone (GET 'site.com/api/foo')
    }
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('spacecraft',)
    http_method_names = ['get']
