import django_filters
from api.models import LauncherDetail, Orbiter, Agency

from api.v2.serializers import OrbiterSerializer, LauncherDetailSerializer, AgencySerializer
from rest_framework import viewsets
from rest_framework import permissions


class AgencyViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Launcher to be viewed.

    GET:
    Return a list of all the existing users.
    """
    queryset = Agency.objects.all()
    serializer_class = AgencySerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class LaunchersViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Launchers to be viewed.

    GET:
    Return a list of all the existing launchers.

    FILTERS:
    'family', 'agency', 'name', 'launch_agency__agency', 'full_name'
    """
    queryset = LauncherDetail.objects.all()
    serializer_class = LauncherDetailSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filter_fields = ('family', 'agency', 'name', 'launch_agency__agency', 'full_name',)


class OrbiterViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Orbiters to be viewed.

    GET:
    Return a list of all the existing orbiters.
    """
    queryset = Orbiter.objects.all()
    serializer_class = OrbiterSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)