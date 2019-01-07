from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from api.models import *
from api.permission import HasGroupPermission
from api.v330.spacecraft.serializers import SpacecraftDetailedSerializer, SpacecraftSerializer


# TODO docs and filters
class SpacecraftViewSet(ModelViewSet):
    """
    API endpoint that allows Spacecrafts to be viewed.
    A Spacecraft is a physically manufactured instance of a Spacecraft Configuration

    GET:
    Return a list of all the existing spacecraft.

    FILTERS:
    Parameters - 'name', 'status', 'spacecraft_config'
    Example - /api/3.3.0/spacecraft/?status=Active

    SEARCH EXAMPLE:
    Example - /api/3.3.0/spacecraft/?search=Dragon

    ORDERING:
    Fields - 'id'
    Example - /api/3.3.0/spacecraft/?order=id
    """

    def get_serializer_class(self):
        mode = self.request.query_params.get("mode", "normal")
        if self.action == 'retrieve' or mode == "detailed":
            return SpacecraftDetailedSerializer
        else:
            return SpacecraftSerializer

    queryset = Spacecraft.objects.all()
    permission_classes = [HasGroupPermission]
    permission_groups = {
        'retrieve': ['_Public'], # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public'] # list returns None and is therefore NOT accessible by anyone (GET 'site.com/api/foo')
    }
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filter_fields = ('name', 'status', 'spacecraft_config')
    search_fields = ('$name', 'spacecraft_config__name',)
    ordering_fields = ('id', )