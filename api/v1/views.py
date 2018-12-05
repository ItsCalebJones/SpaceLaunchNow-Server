import django_filters
from rest_framework import permissions
from rest_framework import viewsets

from api.models import LauncherConfig, SpacecraftConfiguration, Agency
from api.permission import HasGroupPermission
from api.v1.serializers import OrbiterSerializer, LauncherDetailSerializer, AgencySerializer


class AgencyViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Launcher to be viewed.

    GET:
    Return a list of all the existing users.
    """
    queryset = Agency.objects.filter(featured=True).distinct()
    serializer_class = AgencySerializer
    permission_classes = [HasGroupPermission]
    permission_groups = {
        'retrieve': ['_Public'],  # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public']
    }


class LauncherDetailViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Launchers to be viewed.

    GET:
    Return a list of all the existing launchers.

    FILTERS:
    'family', 'name', 'launch_agency__agency', 'full_name'
    """
    queryset = LauncherConfig.objects.all()
    serializer_class = LauncherDetailSerializer
    permission_classes = [HasGroupPermission]
    permission_groups = {
        'retrieve': ['_Public'],  # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public']
    }
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filter_fields = ('family', 'name', 'launch_agency__name', 'full_name',)


class OrbiterViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Orbiters to be viewed.

    GET:
    Return a list of all the existing orbiters.
    """
    queryset = SpacecraftConfiguration.objects.all()
    serializer_class = OrbiterSerializer
    permission_classes = [HasGroupPermission]
    permission_groups = {
        'retrieve': ['_Public'],  # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public']
    }
