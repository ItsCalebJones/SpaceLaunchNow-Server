from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from api.models import *
from api.permission import HasGroupPermission
from api.v330.launcher.serializers import LauncherDetailSerializer, LauncherSerializer


class LauncherViewSet(ModelViewSet):
    """
    API endpoint that allows Launcher instances to be viewed.

    GET:
    Return a list of all the existing launcher instances.

    FILTERS:
    Parameters - 'id', 'serial_number'
    Example - /3.3.0/launcher/?serial_number=B1046
    """

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return LauncherDetailSerializer
        else:
            return LauncherSerializer

    queryset = Launcher.objects.all()
    permission_classes = [HasGroupPermission]
    permission_groups = {

        'retrieve': ['_Public'],  # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public']
    }
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('id', 'serial_number',)
