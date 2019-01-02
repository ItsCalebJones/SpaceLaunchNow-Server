from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from api.models import *
from api.permission import HasGroupPermission
from api.v330.spacestation.serializers import SpaceStationDetailedSerializer, SpaceStationSerializer


# TODO docs
class SpaceStationViewSet(ModelViewSet):
    """
    API endpoint that allows Space Stations to be viewed.

    GET:
    Return a list of all the existing space stations.
    """
    def get_serializer_class(self):
        if self.action == 'retrieve':
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
    filter_fields = ('name', 'status')
    search_fields = ('$name', 'spacecraft_config__name',)
    ordering_fields = ('id', )