import pytz
from django.db.models import Q, Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from zinnia.models import Entry
from api.v321.detailed.serializers import AgencySerializerDetailed, LauncherConfigDetailSerializer,\
    OrbiterDetailSerializer, LaunchDetailedSerializer
from api.v321.list.serializers import LaunchListSerializer
from api.v321.normal.serializers import EntrySerializer, AgencySerializer, EventsSerializer, LaunchSerializer, \
    LauncherDetailedSerializer
from api.models import *
from datetime import datetime, timedelta
from api.models import LauncherConfig, OrbiterConfiguration, Agency
from api.permission import HasGroupPermission
from bot.models import Launch


class EntryViewSet(ModelViewSet):
    """
    API endpoint that allows News posts to be viewed.

    """
    queryset = Entry.objects.order_by('-publication_date').filter(status=2).all()

    # serializer_class = AgencySerializer

    def get_serializer_class(self):
        return EntrySerializer

    permission_classes = [HasGroupPermission]
    permission_groups = {
        'create': ['Developers'],  # Developers can POST
        'destroy': ['Developers'],  # Developers can DELETE
        'partial_update': ['Contributors', 'Developers'],  # Designers and Developers can PATCH
        'retrieve': ['_Public'],  # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public']
    }
    # filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    # filter_fields = ('featured',)
    # search_fields = ('^name',)
    # ordering_fields = ('id', 'name', 'featured')


class AgencyViewSet(ModelViewSet):
    """
    API endpoint that allows Agencies to be viewed.

    GET:
    Return a list of all the existing users.

    FILTERS:
    Parameters - 'featured', 'launch_library_id', 'detailed', 'orbiters'
    Example - /3.2.0/agencies/?featured=true&launch_library_id=44&detailed

    SEARCH EXAMPLE:
    /3.2.0/agencies/?search=nasa

    ORDERING:
    Fields - 'id', 'name', 'featured', 'launch_library_id'
    Example - /3.2.0/agencies/?ordering=featured

    """

    def get_queryset(self):
        orbiters = self.request.query_params.get("orbiters", False)
        if orbiters:
            return Agency.objects.annotate(orbiter_count=Count('orbiter_list')).filter(orbiter_count__gt=0)
        else:
            return Agency.objects.all()

    def get_serializer_class(self):
        mode = self.request.query_params.get("mode", "normal")
        orbiters = self.request.query_params.get("orbiters", False)
        if mode == "detailed":
            return AgencySerializerDetailed
        if orbiters:
            return AgencySerializerDetailed
        else:
            return AgencySerializer

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
    ordering_fields = ('id', 'name', 'featured')


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
    queryset = LauncherConfig.objects.all()
    serializer_class = LauncherConfigDetailSerializer
    permission_classes = [HasGroupPermission]
    permission_groups = {

        'retrieve': ['_Public'],  # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public']
    }
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('family', 'name', 'launch_agency__name', 'full_name', 'id')


class LauncherViewSet(ModelViewSet):
    """
    API endpoint that allows Launcher instances to be viewed.

    GET:
    Return a list of all the existing launcher instances.

    FILTERS:

    Get all Launchers with the Launch Library ID of 44.
    Example - /3.2.0/launcher

    Get all Launchers with the Agency with name NASA.
    Example - /3.2.0/launcher/?launch_agency__name=NASA
    """
    queryset = Launcher.objects.all()
    serializer_class = LauncherDetailedSerializer
    permission_classes = [HasGroupPermission]
    permission_groups = {

        'retrieve': ['_Public'],  # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public']
    }
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('id', 'serial_number',)


class OrbiterViewSet(ModelViewSet):
    """
    API endpoint that allows Orbiters to be viewed.

    GET:
    Return a list of all the existing orbiters.
    """
    queryset = OrbiterConfiguration.objects.all()
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
    Fields - 'name', 'id(s)', 'lsp_id', 'lsp_name', 'serial_number', 'launcher_config__id',

    MODE:
    'normal', 'list', 'detailed'
    EXAMPLE: ?mode=list

    SEARCH:
    Searches through the launch name, rocket name, launch agency and mission name.
    EXAMPLE - ?search=SpaceX
    """

    def get_queryset(self):
        ids = self.request.query_params.get('id', None)
        lsp_name = self.request.query_params.get('lsp__name', None)
        lsp_id = self.request.query_params.get('lsp__id', None)
        serial_number = self.request.query_params.get('serial_number', None)
        launcher_config__id = self.request.query_params.get('launcher_config__id', None)
        location_filters = self.request.query_params.get('location__ids', None)
        lsp_filters = self.request.query_params.get('lsp__ids', None)
        related = self.request.query_params.get('related', None)

        if location_filters and lsp_filters:
            lsp_filters = lsp_filters.split(',')
            location_filters = location_filters.split(',')
            return Launch.objects.filter(Q(rocket__configuration__launch_agency__id__in=lsp_filters) | Q(
                pad__location__id__in=location_filters)).prefetch_related(
                'info_urls').prefetch_related('vid_urls').select_related('rocket').select_related(
                'mission').select_related('pad').select_related('pad__location').prefetch_related(
                'rocket__configuration').prefetch_related('rocket__configuration__launch_agency').prefetch_related(
                'mission__mission_type').prefetch_related('rocket__firststage').select_related(
                'rocket__configuration__launch_agency').order_by('net')
        if lsp_filters:
            lsp_filters = lsp_filters.split(',')
            return Launch.objects.filter(rocket__configuration__launch_agency__id__in=lsp_filters).prefetch_related(
                'info_urls').prefetch_related('vid_urls').select_related('rocket').select_related(
                'mission').select_related('pad').select_related('pad__location').prefetch_related(
                'rocket__configuration').prefetch_related('rocket__configuration__launch_agency').prefetch_related(
                'mission__mission_type').prefetch_related('rocket__firststage').select_related(
                'rocket__configuration__launch_agency').order_by('net')

        if location_filters:
            location_filters = location_filters.split(',')
            return Launch.objects.filter(pad__location__id__in=location_filters).prefetch_related(
                'info_urls').prefetch_related('vid_urls').select_related('rocket').select_related(
                'mission').select_related('pad').select_related('pad__location').prefetch_related(
                'rocket__configuration').prefetch_related('rocket__configuration__launch_agency').prefetch_related(
                'mission__mission_type').prefetch_related('rocket__firststage').select_related(
                'rocket__configuration__launch_agency').order_by('net')
        if ids:
            ids = ids.split(',')
            return Launch.objects.filter(id__in=ids).prefetch_related(
                'info_urls').prefetch_related('vid_urls').select_related('rocket').select_related(
                'mission').select_related('pad').select_related('pad__location').prefetch_related(
                'rocket__configuration').prefetch_related('rocket__configuration__launch_agency').prefetch_related(
                'mission__mission_type').prefetch_related('rocket__firststage').select_related(
                'rocket__configuration__launch_agency').order_by('net')
        if serial_number:
            return Launch.objects.filter(rocket__firststage__launcher__serial_number=serial_number).prefetch_related(
                'info_urls').prefetch_related('vid_urls').select_related('rocket').select_related(
                'mission').select_related('pad').select_related('pad__location').prefetch_related(
                'rocket__configuration').prefetch_related('rocket__configuration__launch_agency').prefetch_related(
                'mission__mission_type').prefetch_related('rocket__firststage').select_related(
                'rocket__configuration__launch_agency')
        if lsp_name:
            launches = Launch.objects.filter(Q(rocket__configuration__launch_agency__name__icontains=lsp_name)
                                             | Q(rocket__configuration__launch_agency__abbrev__icontains=lsp_name)
                                             ).prefetch_related(
                'info_urls').prefetch_related('vid_urls').select_related('rocket').select_related(
                'mission').select_related('pad').select_related('pad__location').prefetch_related(
                'rocket__configuration').prefetch_related('rocket__configuration__launch_agency').prefetch_related(
                'mission__mission_type').prefetch_related('rocket__firststage').select_related(
                'rocket__configuration__launch_agency')
            total_launches = launches
            if related:
                try:
                    agency = Agency.objects.get(name=lsp_name)
                    related_agency = agency.related_agencies.all()
                    for related in related_agency:
                        related_launches = Launch.objects.filter(rocket__configuration__launch_agency__id=related.id)
                        total_launches = launches | related_launches
                except Agency.DoesNotExist:
                    print("Cant find agency.")
            return total_launches.order_by('net')
        if lsp_id:
            launches = Launch.objects.filter(rocket__configuration__launch_agency__id=lsp_id).prefetch_related(
                'info_urls').prefetch_related('vid_urls').select_related('rocket').select_related(
                'mission').select_related('pad').select_related('pad__location').prefetch_related(
                'rocket__configuration').prefetch_related('rocket__configuration__launch_agency').prefetch_related(
                'mission__mission_type').prefetch_related('rocket__firststage').select_related(
                'rocket__configuration__launch_agency')
            total_launches = launches
            if related:
                try:
                    agency = Agency.objects.get(name=lsp_id)
                    related_agency = agency.related_agencies.all()
                    for related in related_agency:
                        related_launches = Launch.objects.filter(rocket__configuration__launch_agency__id=related.id)
                        total_launches = launches | related_launches
                except Agency.DoesNotExist:
                    print("Cant find agency.")
            return total_launches.order_by('net')
        if launcher_config__id:
            return Launch.objects.filter(rocket__configuration__id=launcher_config__id).prefetch_related(
                'info_urls').prefetch_related('vid_urls').select_related('rocket').select_related(
                'mission').select_related('pad').select_related('pad__location').prefetch_related(
                'rocket__configuration').prefetch_related('rocket__configuration__launch_agency').prefetch_related(
                'mission__mission_type').prefetch_related('rocket__firststage').select_related(
                'rocket__configuration__launch_agency')
        else:
            return Launch.objects.order_by('net').prefetch_related(
                'info_urls').prefetch_related('vid_urls').select_related('rocket').select_related(
                'mission').select_related('pad').select_related('pad__location').prefetch_related(
                'rocket__configuration').prefetch_related('rocket__configuration__launch_agency').prefetch_related(
                'mission__mission_type').prefetch_related('rocket__firststage').select_related(
                'rocket__configuration__launch_agency').all()

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
    filter_fields = ('name', 'rocket__configuration__name', 'rocket__configuration__launch_agency__name', 'status')
    search_fields = ('$name', '$rocket__configuration__name', '$rocket__configuration__launch_agency__name',
                     '$rocket__configuration__launch_agency__abbrev', '$mission__name', '$pad__location__name',
                     '$pad__name')
    ordering_fields = ('id', 'name', 'net',)


class UpcomingLaunchViewSet(ModelViewSet):
    """
    API endpoint that returns future Launch objects and launches from the last twenty four hours.

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
        ids = self.request.query_params.get('id', None)
        lsp_name = self.request.query_params.get('lsp__name', None)
        lsp_id = self.request.query_params.get('lsp__id', None)
        serial_number = self.request.query_params.get('serial_number', None)
        launcher_config__id = self.request.query_params.get('launcher_config__id', None)
        related = self.request.query_params.get('related', None)
        now = datetime.now()
        now = now - timedelta(days=1)

        location_filters = self.request.query_params.get('location__ids', None)
        lsp_filters = self.request.query_params.get('lsp__ids', None)

        if location_filters and lsp_filters:
            lsp_filters = lsp_filters.split(',')
            location_filters = location_filters.split(',')
            return Launch.objects.filter(net__gte=now).filter(Q(rocket__configuration__launch_agency__id__in=lsp_filters) | Q(
                pad__location__id__in=location_filters)).prefetch_related(
                'info_urls').prefetch_related('vid_urls').select_related('rocket').select_related(
                'mission').select_related('pad').select_related('pad__location').prefetch_related(
                'rocket__configuration').prefetch_related('rocket__configuration__launch_agency').prefetch_related(
                'mission__mission_type').prefetch_related('rocket__firststage').select_related(
                'rocket__configuration__launch_agency').order_by('net')
        if lsp_filters:
            lsp_filters = lsp_filters.split(',')
            return Launch.objects.filter(net__gte=now).filter(rocket__configuration__launch_agency__id__in=lsp_filters).prefetch_related(
                'info_urls').prefetch_related('vid_urls').select_related('rocket').select_related(
                'mission').select_related('pad').select_related('pad__location').prefetch_related(
                'rocket__configuration').prefetch_related('rocket__configuration__launch_agency').prefetch_related(
                'mission__mission_type').prefetch_related('rocket__firststage').select_related(
                'rocket__configuration__launch_agency').order_by('net')

        if location_filters:
            location_filters = location_filters.split(',')
            return Launch.objects.filter(net__gte=now).filter(pad__location__id__in=location_filters).prefetch_related(
                'info_urls').prefetch_related('vid_urls').select_related('rocket').select_related(
                'mission').select_related('pad').select_related('pad__location').prefetch_related(
                'rocket__configuration').prefetch_related('rocket__configuration__launch_agency').prefetch_related(
                'mission__mission_type').prefetch_related('rocket__firststage').select_related(
                'rocket__configuration__launch_agency').order_by('net')

        if ids:
            ids = ids.split(',')
            return Launch.objects.filter(net__gte=now).filter(id__in=ids).prefetch_related(
                'info_urls').prefetch_related('vid_urls').select_related('rocket').select_related(
                'mission').select_related('pad').select_related('pad__location').prefetch_related(
                'rocket__configuration').prefetch_related('rocket__configuration__launch_agency').prefetch_related(
                'mission__mission_type').prefetch_related('rocket__firststage').select_related(
                'rocket__configuration__launch_agency').order_by('net')
        if serial_number:
            return Launch.objects.filter(
                net__gte=now).filter(rocket__firststage__launcher__serial_number=serial_number).prefetch_related(
                'info_urls').prefetch_related('vid_urls').select_related('rocket').select_related(
                'mission').select_related('pad').select_related('pad__location').prefetch_related(
                'rocket__configuration').prefetch_related('rocket__configuration__launch_agency').prefetch_related(
                'mission__mission_type').prefetch_related('rocket__firststage').select_related(
                'rocket__configuration__launch_agency').order_by('-net')
        if lsp_name:
            launches = Launch.objects.filter(net__gte=now).filter(
                Q(rocket__configuration__launch_agency__name__icontains=lsp_name)
                | Q(rocket__configuration__launch_agency__abbrev__icontains=lsp_name)).prefetch_related(
                'info_urls').prefetch_related('vid_urls').select_related('rocket').select_related(
                'mission').select_related('pad').select_related('pad__location').prefetch_related(
                'rocket__configuration').prefetch_related('rocket__configuration__launch_agency').prefetch_related(
                'mission__mission_type').prefetch_related('rocket__firststage').select_related(
                'rocket__configuration__launch_agency')
            total_launches = launches
            if related:
                try:
                    agency = Agency.objects.get(name=lsp_name)
                    related_agency = agency.related_agencies.all()
                    for related in related_agency:
                        related_launches = Launch.objects.filter(net__gte=now).filter(
                            rocket__configuration__launch_agency__id=related.id)
                        total_launches = launches | related_launches
                except Agency.DoesNotExist:
                    print("Cant find agency.")
            return total_launches.order_by('net')
        if lsp_id:
            launches = Launch.objects.filter(net__gte=now).filter(rocket__configuration__launch_agency__id=lsp_id).prefetch_related(
                'info_urls').prefetch_related('vid_urls').select_related('rocket').select_related(
                'mission').select_related('pad').select_related('pad__location').prefetch_related(
                'rocket__configuration').prefetch_related('rocket__configuration__launch_agency').prefetch_related(
                'mission__mission_type').prefetch_related('rocket__firststage').select_related(
                'rocket__configuration__launch_agency')
            total_launches = launches
            if related:
                try:
                    agency = Agency.objects.get(name=lsp_id)
                    related_agency = agency.related_agencies.all()
                    for related in related_agency:
                        related_launches = Launch.objects.filter(net__gte=now).filter(
                            rocket__configuration__launch_agency__id=related.id)
                        total_launches = launches | related_launches
                except Agency.DoesNotExist:
                    print("Cant find agency.")
            return total_launches.order_by('net')
        if launcher_config__id:
            return Launch.objects.filter(net__gte=now).filter(
                rocket__configuration__id=launcher_config__id).prefetch_related(
                'info_urls').prefetch_related('vid_urls').select_related('rocket').select_related(
                'mission').select_related('pad').select_related('pad__location').prefetch_related(
                'rocket__configuration').prefetch_related('rocket__configuration__launch_agency').prefetch_related(
                'mission__mission_type').prefetch_related('rocket__firststage').select_related(
                'rocket__configuration__launch_agency')

        else:
            return Launch.objects.filter(net__gte=now).prefetch_related(
                'info_urls').prefetch_related('vid_urls').select_related('rocket').select_related(
                'mission').select_related('pad').select_related('pad__location').prefetch_related(
                'rocket__configuration').prefetch_related('rocket__configuration__launch_agency').prefetch_related(
                'mission__mission_type').prefetch_related('rocket__firststage').select_related(
                'rocket__configuration__launch_agency').order_by('net').all()

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
    filter_fields = ('name', 'rocket__configuration__name', 'rocket__configuration__launch_agency__name', 'status')
    search_fields = ('$name', '$rocket__configuration__name', '$rocket__configuration__launch_agency__name',
                     '$rocket__configuration__launch_agency__abbrev', '$mission__name', '$pad__location__name',
                     '$pad__name')
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
        ids = self.request.query_params.get('id', None)
        lsp_name = self.request.query_params.get('lsp__name', None)
        lsp_id = self.request.query_params.get('lsp__id', None)
        serial_number = self.request.query_params.get('serial_number', None)
        launcher_config__id = self.request.query_params.get('launcher_config__id', None)
        related = self.request.query_params.get('related', None)
        location_filters = self.request.query_params.get('location__ids', None)
        lsp_filters = self.request.query_params.get('lsp__ids', None)

        now = datetime.now()

        if location_filters and lsp_filters:
            lsp_filters = lsp_filters.split(',')
            location_filters = location_filters.split(',')
            return Launch.objects.filter(net__lte=now).filter(Q(rocket__configuration__launch_agency__id__in=lsp_filters) | Q(
                pad__location__id__in=location_filters)).prefetch_related(
                'info_urls').prefetch_related('vid_urls').select_related('rocket').select_related(
                'mission').select_related('pad').select_related('pad__location').prefetch_related(
                'rocket__configuration').prefetch_related('rocket__configuration__launch_agency').prefetch_related(
                'mission__mission_type').prefetch_related('rocket__firststage').select_related(
                'rocket__configuration__launch_agency').order_by('net')
        if lsp_filters:
            lsp_filters = lsp_filters.split(',')
            return Launch.objects.filter(net__lte=now).filter(rocket__configuration__launch_agency__id__in=lsp_filters).prefetch_related(
                'info_urls').prefetch_related('vid_urls').select_related('rocket').select_related(
                'mission').select_related('pad').select_related('pad__location').prefetch_related(
                'rocket__configuration').prefetch_related('rocket__configuration__launch_agency').prefetch_related(
                'mission__mission_type').prefetch_related('rocket__firststage').select_related(
                'rocket__configuration__launch_agency').order_by('net')

        if location_filters:
            location_filters = location_filters.split(',')
            return Launch.objects.filter(net__lte=now).filter(pad__location__id__in=location_filters).prefetch_related(
                'info_urls').prefetch_related('vid_urls').select_related('rocket').select_related(
                'mission').select_related('pad').select_related('pad__location').prefetch_related(
                'rocket__configuration').prefetch_related('rocket__configuration__launch_agency').prefetch_related(
                'mission__mission_type').prefetch_related('rocket__firststage').select_related(
                'rocket__configuration__launch_agency').order_by('net')
        if ids:
            ids = ids.split(',')
            return Launch.objects.filter(id__in=ids).filter(net__lte=now).order_by('-net')
        if serial_number:
            return Launch.objects.filter(rocket__firststage__launcher__serial_number=serial_number).filter(
                net__lte=now).order_by('-net')
        if lsp_name:
            launches = Launch.objects.filter(net__lte=now).filter(
                Q(rocket__configuration__launch_agency__name__icontains=lsp_name)
                | Q(rocket__configuration__launch_agency__abbrev__icontains=lsp_name)).prefetch_related(
                'info_urls').prefetch_related('vid_urls').select_related('rocket').select_related(
                'mission').select_related('pad').select_related('pad__location').prefetch_related(
                'rocket__configuration').prefetch_related('rocket__configuration__launch_agency').prefetch_related(
                'mission__mission_type').prefetch_related('rocket__firststage').select_related(
                'rocket__configuration__launch_agency')
            total_launches = launches
            if related:
                try:
                    agency = Agency.objects.get(name=lsp_name)
                    related_agency = agency.related_agencies.all()
                    for related in related_agency:
                        related_launches = Launch.objects.filter(
                            rocket__configuration__launch_agency__id=related.id).filter(net__lte=now)
                        total_launches = launches | related_launches
                except Agency.DoesNotExist:
                    print("Cant find agency.")
            return total_launches.order_by('-net')
        if lsp_id:
            launches = Launch.objects.filter(net__lte=now).filter(
                rocket__configuration__launch_agency__id=lsp_id).prefetch_related(
                'info_urls').prefetch_related('vid_urls').select_related('rocket').select_related(
                'mission').select_related('pad').select_related('pad__location').prefetch_related(
                'rocket__configuration').prefetch_related('rocket__configuration__launch_agency').prefetch_related(
                'mission__mission_type').prefetch_related('rocket__firststage').select_related(
                'rocket__configuration__launch_agency')
            total_launches = launches
            if related:
                try:
                    agency = Agency.objects.get(id=lsp_id)
                    related_agency = agency.related_agencies.all()
                    for related in related_agency:
                        related_launches = Launch.objects.filter(net__lte=now).filter(
                            rocket__configuration__launch_agency__id=related.id)
                        total_launches = launches | related_launches
                except Agency.DoesNotExist:
                    print("Cant find agency.")
            return total_launches.order_by('-net')
        if launcher_config__id:
            return Launch.objects.filter(net__lte=now).filter(
                rocket__configuration__id=launcher_config__id).prefetch_related(
                'info_urls').prefetch_related('vid_urls').select_related('rocket').select_related(
                'mission').select_related('pad').select_related('pad__location').prefetch_related(
                'rocket__configuration').prefetch_related('rocket__configuration__launch_agency').prefetch_related(
                'mission__mission_type').prefetch_related('rocket__firststage').select_related(
                'rocket__configuration__launch_agency')
        else:
            return Launch.objects.filter(net__lte=now).prefetch_related(
                'info_urls').prefetch_related('vid_urls').select_related('rocket').select_related(
                'mission').select_related('pad').select_related('pad__location').prefetch_related(
                'rocket__configuration').prefetch_related('rocket__configuration__launch_agency').prefetch_related(
                'mission__mission_type').prefetch_related('rocket__firststage').select_related(
                'rocket__configuration__launch_agency').order_by('-net').all()

    def get_serializer_class(self):
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
    filter_fields = ('name', 'rocket__configuration__name', 'rocket__configuration__launch_agency__name', 'status')
    search_fields = ('$name', '$rocket__configuration__name', '$rocket__configuration__launch_agency__name',
                     '$rocket__configuration__launch_agency__abbrev', '$mission__name', '$pad__location__name',
                     '$pad__name')
    ordering_fields = ('id', 'name', 'net',)
