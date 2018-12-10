import pytz
from django.db.models import Prefetch
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter

from api.v300.serializers import *
from datetime import datetime, timedelta
from api.models import LauncherConfig, SpacecraftConfiguration, Agency
from api.permission import HasGroupPermission
from bot.models import Launch


class AgencyViewSet(ModelViewSet):
    """
    API endpoint that allows Agencies to be viewed.

    GET:
    Return a list of all the existing users.

    FILTERS:
    Parameters - 'featured', 'launch_library_id', 'detailed'
    Example - /3.0.0/agencies/?featured=true&launch_library_id=44&detailed

    SEARCH EXAMPLE:
    /3.0.0/agencies/?search=nasa

    ORDERING:
    Fields - 'id', 'name', 'featured', 'launch_library_id'
    Example - /v300/agencies/?ordering=featured

    """
    queryset = Agency.objects.all()

    # serializer_class = AgencySerializer

    def get_serializer_class(self):
        print(self.request.query_params.keys())
        mode = self.request.query_params.get("mode", "normal")
        if mode == "detailed":
            return AgencyDetailedSerializer
        else:
            return AgencySerializer

    permission_classes = [HasGroupPermission]
    permission_groups = {
        'retrieve': ['_Public'],  # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public']
    }
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filter_fields = ('featured',)
    search_fields = ('^name',)
    ordering_fields = ('id', 'name', 'featured')


class LaunchersViewSet(ModelViewSet):
    """
    API endpoint that allows Launchers to be viewed.

    GET:
    Return a list of all the existing launchers.

    FILTERS:
    Fields - 'family', 'agency', 'name', 'launch_agency__name', 'full_name', 'launch_agency__launch_library_id'

    Get all Launchers with the Agency with name NASA.
    Example - /3.0.0/launchers/?launch_agency__name=NASA
    """
    queryset = LauncherConfig.objects.all()
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
    filter_fields = ('family', 'name', 'launch_agency__name', 'full_name', 'id')
    lookup_field = 'launch_library_id'


class OrbiterViewSet(ModelViewSet):
    """
    API endpoint that allows Orbiters to be viewed.

    GET:
    Return a list of all the existing orbiters.
    """
    queryset = SpacecraftConfiguration.objects.all()
    serializer_class = OrbiterDetailSerializer
    permission_classes = [HasGroupPermission]
    permission_groups = {
        'retrieve': ['_Public'],  # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public']  # list returns None and is therefore NOT accessible by anyone (GET 'site.com/api/foo')
    }


class EventViewSet(ModelViewSet):
    """
    API endpoint that allows Events to be viewed.

    GET:
    Return a list of future Events
    """
    now = datetime.now(tz=pytz.utc)
    queryset = Events.objects.filter(date__gte=now)
    serializer_class = EventsSerializer
    permission_classes = [HasGroupPermission]
    permission_groups = {
        'retrieve': ['_Public'],  # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public']  # list returns None and is therefore NOT accessible by anyone (GET 'site.com/api/foo')
    }


class LaunchViewSet(ModelViewSet):
    """
    API endpoint that returns all Launch objects or a single launch.

    EXAMPLE - /launch/<id>/ or /launch/?mode=list&search=SpaceX

    GET:
    Return a list of all Launch objects.

    FILTERS:
    Fields - 'name', 'id(s)', 'lsp_id', 'lsp_name', 'launcher_config__id',

    MODE:
    'normal', 'list', 'detailed'
    EXAMPLE: ?mode=list

    SEARCH:
    Searches through the launch name, rocket name, launch agency and mission name.
    EXAMPLE - ?search=SpaceX
    """

    def get_queryset(self):
        ids = self.request.query_params.get('id', None)
        lsp_id = self.request.query_params.get('lsp_id', None)
        lsp_name = self.request.query_params.get('lsp_name', None)
        launcher_config__id = self.request.query_params.get('launcher_config__id', None)
        if ids:
            ids = ids.split(',')
            return Launch.objects.filter(launch_library_id__in=ids)
        elif lsp_id:
            return Launch.objects.filter(rocket__configuration__launch_agency__id=lsp_id).filter(launch_library=True)
        elif lsp_name:
            return Launch.objects.filter(Q(rocket__configuration__launch_agency__name__icontains=lsp_name)
                                         | Q(rocket__configuration__launch_agency__abbrev__icontains=lsp_name)).filter(launch_library=True)
        elif launcher_config__id:
            return Launch.objects.filter(rocket__configuration__id=launcher_config__id).filter(launch_library=True)
        else:
            return Launch.objects.order_by('net').prefetch_related('info_urls').prefetch_related(
                'vid_urls').prefetch_related('rocket').prefetch_related('pad__location').select_related(
                'mission').select_related('pad').filter(launch_library=True)

    def get_serializer_class(self):
        print(self.request.query_params.keys())
        mode = self.request.query_params.get("mode", "normal")
        if mode == "detailed":
            return LaunchDetailedSerializer
        elif mode == "list":
            return LaunchListSerializer
        else:
            return LaunchSerializer

    permission_classes = [HasGroupPermission]
    permission_groups = {
        'retrieve': ['_Public'],  # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public']  # list returns None and is therefore NOT accessible by anyone (GET 'site.com/api/foo')
    }
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filter_fields = ('name',)
    search_fields = ('$name', '$rocket__configuration__name', '$rocket__configuration__launch_agency__name',
                     '$mission__name')
    ordering_fields = ('launch_library_id', 'name', 'net',)
    lookup_field = 'launch_library_id'


class UpcomingLaunchViewSet(ModelViewSet):
    """
    API endpoint that returns future Launch objects.

    GET:
    Return a list of future Launches

    FILTERS:
    Fields - 'name', 'id(s)', 'lsp_id', 'lsp_name', 'launcher_config__id',

    MODE:
    'normal', 'list', 'detailed'
    EXAMPLE: ?mode=list

    SEARCH:
    Searches through the launch name, rocket name, launch agency and mission name.
    EXAMPLE - ?search=SpaceX
    """

    def get_queryset(self):
        now = datetime.now()
        now = now - timedelta(days=1)
        ids = self.request.query_params.get('id', None)
        lsp_id = self.request.query_params.get('lsp_id', None)
        lsp_name = self.request.query_params.get('lsp_name', None)
        launcher_config__id = self.request.query_params.get('launcher_config__id', None)
        if ids:
            ids = ids.split(',')
            return Launch.objects.filter(launch_library_id__in=ids).filter(net__gte=now).filter(launch_library=True).order_by('net')
        elif lsp_id:
            return Launch.objects.filter(rocket__configuration__launch_agency__id=lsp_id).filter(net__gte=now).filter(launch_library=True)
        elif lsp_name:
            return Launch.objects.filter(Q(rocket__configuration__launch_agency__name__icontains=lsp_name)
                                         | Q(rocket__configuration__launch_agency__abbrev__icontains=lsp_name)).filter(
                net__gte=now).filter(launch_library=True)
        elif launcher_config__id:
            return Launch.objects.filter(rocket__configuration__id=launcher_config__id).filter(net__gte=now).filter(launch_library=True)
        else:
            return Launch.objects.filter(net__gte=now).prefetch_related('info_urls').prefetch_related(
                'vid_urls').prefetch_related('rocket').prefetch_related(
                'pad__location').select_related('mission').select_related('pad').order_by('net').filter(launch_library=True)

    def get_serializer_class(self):
        print(self.request.query_params.keys())
        mode = self.request.query_params.get("mode", "normal")
        if mode == "detailed":
            return LaunchDetailedSerializer
        elif mode == "list":
            return LaunchListSerializer
        else:
            return LaunchSerializer

    now = datetime.now()
    permission_classes = [HasGroupPermission]
    permission_groups = {
        'retrieve': ['_Public'],  # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public']  # list returns None and is therefore NOT accessible by anyone (GET 'site.com/api/foo')
    }
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filter_fields = ('name',)
    search_fields = ('$name', '$rocket__configuration__name', '$rocket__configuration__launch_agency__name',
                     '$mission__name')
    ordering_fields = ('id', 'name', 'net',)


class PreviousLaunchViewSet(ModelViewSet):
    """
    API endpoint that returns previous Launch objects.

    GET:
    Return a list of previous Launches

    FILTERS:
    Fields - 'name', 'id(s)', 'lsp_id', 'lsp_name', 'launcher_config__id',

    MODE:
    'normal', 'list', 'detailed'
    EXAMPLE: ?mode=list

    SEARCH:
    Searches through the launch name, rocket name, launch agency and mission name.
    EXAMPLE - ?search=SpaceX
    """

    def get_queryset(self):
        now = datetime.now()

        ids = self.request.query_params.get('id', None)
        lsp_id = self.request.query_params.get('lsp_id', None)
        lsp_name = self.request.query_params.get('lsp_name', None)
        launcher_config__id = self.request.query_params.get('launcher_config__id', None)
        if ids:
            ids = ids.split(',')
            return Launch.objects.filter(launch_library_id__in=ids).filter(net__lte=now).filter(launch_library=True)
        elif lsp_id:
            return Launch.objects.filter(rocket__configuration__launch_agency__id=lsp_id).filter(net__lte=now).filter(launch_library=True)
        elif lsp_name:
            return Launch.objects.filter(Q(rocket__configuration__launch_agency__name__icontains=lsp_name)
                                         | Q(rocket__configuration__launch_agency__abbrev__icontains=lsp_name)).filter(
                net__lte=now).filter(launch_library=True)
        elif launcher_config__id:
            return Launch.objects.filter(rocket__configuration__id=launcher_config__id).filter(net__lte=now).filter(launch_library=True)
        else:
            return Launch.objects.filter(net__lte=now).prefetch_related('info_urls').prefetch_related(
                'vid_urls').prefetch_related('rocket').prefetch_related(
                'pad__location').select_related('mission').select_related('pad').order_by('-net').filter(launch_library=True)

    def get_serializer_class(self):
        print(self.request.query_params.keys())
        mode = self.request.query_params.get("mode", "normal")
        if mode == "detailed":
            return LaunchDetailedSerializer
        elif mode == "list":
            return LaunchListSerializer
        else:
            return LaunchSerializer

    permission_classes = [HasGroupPermission]
    permission_groups = {
        'retrieve': ['_Public'],  # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public']  # list returns None and is therefore NOT accessible by anyone (GET 'site.com/api/foo')
    }
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filter_fields = ('name',)
    search_fields = ('$name', '$rocket__configuration__name', '$rocket__configuration__launch_agency__name',
                     '$mission__name')
    ordering_fields = ('id', 'name', 'net',)
