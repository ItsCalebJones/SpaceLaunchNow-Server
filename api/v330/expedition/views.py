from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from api.models import *
from api.permission import HasGroupPermission


from api.v330.expedition.serializers import ExpeditionDetailSerializer, ExpeditionSerializer


# TODO docs and filters
class ExpeditionViewSet(ModelViewSet):
    """
    API endpoint that allows Expeditions to be viewed.

    GET:
    Return a list of all the existing expeditions.
    """
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ExpeditionDetailSerializer
        else:
            return ExpeditionSerializer

    queryset = Expedition.objects.all()
    permission_classes = [HasGroupPermission]
    permission_groups = {
        'retrieve': ['_Public'],  # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public']  # list returns None and is therefore NOT accessible by anyone (GET 'site.com/api/foo')
    }