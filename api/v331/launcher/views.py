from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from api.models import *
from api.permission import HasGroupPermission
from api.v331.launcher.serializers import LauncherDetailSerializer, LauncherSerializer


class LauncherViewSet(ModelViewSet):
    """
    API endpoint that allows Launcher instances to be viewed.

    GET:
    Return a list of all the existing launcher instances.

    FILTERS:
    Parameters - 'id', 'serial_number', 'flight_proven', 'launcher_config', 'launcher_config__launch_agency'
    Example - /api/3.3.0/launcher/?serial_number=B1046

    SEARCH EXAMPLE:
    /api/3.3.0/launcher/?search=expended
    Searches through serial number or status

    ORDERING:
    Fields - 'id', 'flight_proven',
    Example - /api/3.3.0/launcher/?order=flight_proven
    """

    def get_serializer_class(self):
        mode = self.request.query_params.get("mode", "normal")
        if self.action == 'retrieve' or mode == "detailed":
            return LauncherDetailSerializer
        else:
            return LauncherSerializer

    queryset = Launcher.objects.all()
    permission_classes = [HasGroupPermission]
    permission_groups = {

        'retrieve': ['_Public'],  # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public']
    }
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filter_fields = ('id', 'serial_number', 'flight_proven', 'launcher_config', 'launcher_config__launch_agency')
    search_fields = ('^serial_number', '^status',)
    ordering_fields = ('id', 'flight_proven',)
