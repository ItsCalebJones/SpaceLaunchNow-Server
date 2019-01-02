from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from api.models import *
from api.permission import HasGroupPermission
from api.v330.spacecraft.serializers import SpacecraftDetailedSerializer, SpacecraftSerializer


# TODO docs and filters
class SpacecraftViewSet(ModelViewSet):

    def get_serializer_class(self):
        if self.action == 'retrieve':
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
    filter_fields = ('name', 'status')
    search_fields = ('$name', 'spacecraft_config__name',)
    ordering_fields = ('id', )