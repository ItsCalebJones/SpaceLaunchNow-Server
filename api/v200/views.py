
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from api.models import LauncherDetail, Orbiter, Agency

from api.v200.serializers import OrbiterSerializer, LauncherDetailSerializer, AgencySerializer
from rest_framework import viewsets
from rest_framework import permissions


class AgencyViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Agencies to be viewed.

    GET:
    Return a list of all the existing users.

    FILTERS:
    Fields - 'featured', 'launch_library_id'
    Example - /2.0.0/agencies/?featured=true&launch_library_id=44

    SEARCH EXAMPLE:
    /2.0.0/agencies/?search=nasa

    ORDERING:
    Fields - 'id', 'name', 'featured', 'launch_library_id'
    Example - /v200/agencies/?ordering=featured

    """
    queryset = Agency.objects.all()
    serializer_class = AgencySerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filter_fields = ('featured', 'launch_library_id')
    search_fields = ('^name',)
    ordering_fields = ('id', 'name', 'featured', 'launch_library_id',)


class LaunchersViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Launchers to be viewed.

    GET:
    Return a list of all the existing launchers.

    FILTERS:
    Fields - 'family', 'agency', 'name', 'launch_agency__name', 'full_name', 'launch_agency__launch_library_id'

    Get all Launchers with the Launch Library ID of 44.
    Example - /2.0.0/launchers/?launch_agency__launch_library_id=44

    Get all Launchers with the Agency with name NASA.
    Example - /2.0.0/launchers/?launch_agency__name=NASA
    """
    queryset = LauncherDetail.objects.all()
    serializer_class = LauncherDetailSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('family', 'agency', 'name', 'launch_agency__name', 'full_name', 'launch_agency__launch_library_id')


class OrbiterViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Orbiters to be viewed.

    GET:
    Return a list of all the existing orbiters.
    """
    queryset = Orbiter.objects.all()
    serializer_class = OrbiterSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)