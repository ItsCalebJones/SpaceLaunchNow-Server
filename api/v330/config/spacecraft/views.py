from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from api.models import *
from api.permission import HasGroupPermission


from api.v330.config.spacecraft.serializers import SpacecraftConfigurationSerializer, SpacecraftConfigurationDetailSerializer


# TODO docs and filters
class SpacecraftConfigViewSet(ModelViewSet):
    """
    API endpoint that allows Spacecraft Configs to be viewed.

    GET:
    Return a list of all the existing spacecraft.
    """
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SpacecraftConfigurationDetailSerializer
        else:
            return SpacecraftConfigurationSerializer

    queryset = SpacecraftConfiguration.objects.all()
    permission_classes = [HasGroupPermission]
    permission_groups = {
        'retrieve': ['_Public'],  # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public']  # list returns None and is therefore NOT accessible by anyone (GET 'site.com/api/foo')
    }