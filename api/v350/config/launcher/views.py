from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from api.models import *
from api.permission import HasGroupPermission


from api.v350.common.serializers import LauncherConfigDetailSerializer, LauncherConfigListSerializer, LauncherConfigSerializer


class LauncherConfigViewSet(ModelViewSet):
    """
    API endpoint that allows Launcher Configurations to be viewed.

    GET:
    Return a list of all the existing launcher configurations.

    MODE:
    Normal and Detailed
    /3.5.0/config/launcher/?mode=detailed

    FILTERS:
    Fields - 'family', 'agency', 'name', 'manufacturer__name', 'full_name', 'manufacturer__launch_library_id'

    Get all Launchers with the Launch Library ID of 44.
    Example - /3.5.0/config/launcher/?manufacturer__launch_library_id=44

    Get all Launchers with the Agency with name NASA.
    Example - /3.5.0/config/launcher/?manufacturer__name=NASA
    """
    def get_serializer_class(self):
        mode = self.request.query_params.get("mode", "normal")
        if self.action == 'retrieve' or mode == "detailed":
            return LauncherConfigDetailSerializer
        elif mode == "list":
            return LauncherConfigListSerializer
        else:
            return LauncherConfigSerializer

    queryset = LauncherConfig.objects.all()
    permission_classes = [HasGroupPermission]
    permission_groups = {
        'retrieve': ['_Public'],  # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public']
    }
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filter_fields = ('family', 'name', 'manufacturer', 'full_name', 'active', 'reusable')
    search_fields = ('^name', '^manufacturer__name', '^full_name', '^description')
    ordering_fields = ('name', 'launch_mass', 'leo_capacity', 'gto_capacity', 'launch_cost')
    http_method_names = ['get']
