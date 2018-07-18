from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter

from api.models import Launcher, Orbiter, Agency, Events

from api.v200.serializers import OrbiterSerializer, LauncherDetailSerializer, AgencyHyperlinkedSerializer, \
     EventsSerializer
from rest_framework import viewsets
from datetime import datetime
from api.models import Launcher, Orbiter, Agency
from api.permission import HasGroupPermission


class AgencyViewSet(ModelViewSet):
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
    serializer_class = AgencyHyperlinkedSerializer

    # # taken directly from the docs for generic APIViews
    # def get_serializer_class(self):
    #     if self.request.query_params.has_key("detailed"):
    #         return AgencyModelSerializer
    #     return AgencyHyperlinkedSerializer

    permission_classes = [HasGroupPermission]
    permission_groups = {
        'create': ['Developers'],  # Developers can POST
        'destroy': ['Developers'],  # Developers can DELETE
        'partial_update': ['Contributors', 'Developers'],  # Designers and Developers can PATCH
        'retrieve': ['_Public'],  # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public']
    }
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filter_fields = ('featured',)
    search_fields = ('^name',)
    ordering_fields = ('id', 'name', 'featured',)


class LaunchersViewSet(ModelViewSet):
    """
    API endpoint that allows Launchers to be viewed.

    GET:
    Return a list of all the existing launchers.

    FILTERS:
    Fields - 'family', 'name', 'launch_agency__name', 'full_name',

    Get all Launchers with the Agency with name NASA.
    Example - /2.0.0/launchers/?launch_agency__name=NASA
    """
    queryset = Launcher.objects.all()
    serializer_class = LauncherDetailSerializer
    permission_classes = [HasGroupPermission]
    permission_groups = {
        'create': ['Developers'],  # Developers can POST
        'destroy': ['Developers'],  # Developers can POST
        'partial_update': ['Contributors', 'Developers'],  # Designers and Developers can PATCH
        'retrieve': ['_Public'],  # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public']
    }
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('family', 'name', 'launch_agency__name', 'full_name',)


class OrbiterViewSet(ModelViewSet):
    """
    API endpoint that allows Orbiters to be viewed.

    GET:
    Return a list of all the existing orbiters.
    """
    queryset = Orbiter.objects.all()
    serializer_class = OrbiterSerializer
    permission_classes = [HasGroupPermission]
    permission_groups = {
        'create': ['Developers'],  # Developers can POST
        'destroy': ['Developers'],  # Developers can POST
        'partial_update': ['Contributors', 'Developers'],  # Designers and Developers can PATCH
        'retrieve': ['_Public'],  # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public']  # list returns None and is therefore NOT accessible by anyone (GET 'site.com/api/foo')
    }


class EventViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Events to be viewed.

    GET:
    Return a list of future Events
    """
    now = datetime.now()
    queryset = Events.objects.filter(date__gte=now)
    serializer_class = EventsSerializer
    permission_classes = [HasGroupPermission]
    permission_groups = {
        'create': ['Developers'],  # Developers can POST
        'destroy': ['Developers'],  # Developers can POST
        'partial_update': ['Contributors', 'Developers'],  # Designers and Developers can PATCH
        'retrieve': ['_Public'],  # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public']  # list returns None and is therefore NOT accessible by anyone (GET 'site.com/api/foo')
    }
