from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from api.models import *
from api.permission import HasGroupPermission


from api.v330.config.launcher.serializers import LauncherConfigDetailSerializer, LauncherConfigSerializer


# TODO docs and filters
class LauncherConfigViewSet(ModelViewSet):
    """
    API endpoint that allows Launcher Configurations to be viewed.

    GET:
    Return a list of all the existing launcher configurations.

    FILTERS:
    Fields - 'family', 'agency', 'name', 'launch_agency__name', 'full_name', 'launch_agency__launch_library_id'

    Get all Launchers with the Launch Library ID of 44.
    Example - /3.2.0/launcher_config/?launch_agency__launch_library_id=44

    Get all Launchers with the Agency with name NASA.
    Example - /3.2.0/launcher_config/?launch_agency__name=NASA
    """
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return LauncherConfigDetailSerializer
        else:
            return LauncherConfigSerializer

    queryset = LauncherConfig.objects.all()
    permission_classes = [HasGroupPermission]
    permission_groups = {

        'retrieve': ['_Public'],  # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public']
    }
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('family', 'name', 'launch_agency__name', 'full_name', 'id')