from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from datetime import datetime, timedelta

from api.models import *
from api.permission import HasGroupPermission
from api.v330.launch.filters import LaunchFilter
from api.v330.launch.serializers import LaunchDetailedSerializer, LaunchListSerializer, LaunchSerializer


class LaunchViewSet(ModelViewSet):
    """
    API endpoint that returns all Launch objects or a single launch.

    EXAMPLE - /launch/<id>/ or /launch/?mode=list&search=SpaceX

    GET:
    Return a list of all Launch objects.

    FILTERS:
    Fields - 'name', 'id(s)', 'lsp_id', 'lsp_name', 'serial_number', 'launcher_config__id', 'rocket__spacecraftflight__spacecraft__name'

    MODE:
    'normal', 'list', 'detailed'
    EXAMPLE: ?mode=list

    SEARCH:
    Searches through the launch name, rocket name, launch agency, mission name & spacecraft name.
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
        is_crewed = self.request.query_params.get('is_crewed', None)
        spacecraft_config_ids = self.request.query_params.get("spacecraft_config__ids", None)

        launches = Launch.objects.all()

        if location_filters and lsp_filters:
            lsp_filters = lsp_filters.split(',')
            location_filters = location_filters.split(',')
            launches = launches.filter(Q(
                rocket__configuration__launch_agency__id__in=lsp_filters) | Q(
                pad__location__id__in=location_filters))

        elif lsp_filters:
            lsp_filters = lsp_filters.split(',')
            launches = launches.filter(
                rocket__configuration__launch_agency__id__in=lsp_filters)

        elif location_filters:
            location_filters = location_filters.split(',')
            launches = launches.filter(
                pad__location__id__in=location_filters)

        if ids:
            ids = ids.split(',')
            launches = launches.filter(id__in=ids)
        if serial_number:
            launches = launches.filter(rocket__firststage__launcher__serial_number=serial_number)
        if is_crewed:
            if is_crewed == 'true':
                launches = launches.filter(rocket__spacecraftflight__launch_crew__isnull=False)
            elif is_crewed == 'false':
                launches = launches.filter(rocket__spacecraftflight__launch_crew__isnull=True)
        if spacecraft_config_ids:
            spacecraft_config_ids = spacecraft_config_ids.split(',')
            launches = launches.filter(rocket__spacecraftflight__spacecraft__spacecraft_config__id__in=spacecraft_config_ids)
        if lsp_name:
            launches = launches.filter(Q(rocket__configuration__launch_agency__name__icontains=lsp_name) |
                                       Q(rocket__configuration__launch_agency__abbrev__icontains=lsp_name))
            if related:
                try:
                    agency = Agency.objects.get(name=lsp_name)
                    related_agency = agency.related_agencies.all()
                    for related in related_agency:
                        related_launches = launches.filter(rocket__configuration__launch_agency__id=related.id)
                        launches = launches | related_launches
                except Agency.DoesNotExist:
                    print("Cant find agency.")
        if lsp_id:
            launches = launches.filter(rocket__configuration__launch_agency__id=lsp_id)
            if related:
                try:
                    agency = Agency.objects.get(name=lsp_id)
                    related_agency = agency.related_agencies.all()
                    for related in related_agency:
                        related_launches = launches.filter(rocket__configuration__launch_agency__id=related.id)
                        launches = launches | related_launches
                except Agency.DoesNotExist:
                    print("Cant find agency.")
        if launcher_config__id:
            launches = launches.filter(rocket__configuration__id=launcher_config__id)

        launches = launches.select_related(
            'rocket__spacecraftflight').select_related(
            'status').prefetch_related(
            'info_urls').prefetch_related('vid_urls').select_related(
            'rocket').select_related(
            'mission').select_related('pad').select_related(
            'pad__location').prefetch_related(
            'rocket__configuration').prefetch_related(
            'rocket__configuration__launch_agency').prefetch_related(
            'mission__mission_type').prefetch_related(
            'rocket__firststage').select_related(
            'rocket__configuration__launch_agency').order_by(
            'net', 'id').distinct()

        return launches

    def get_serializer_class(self):
        mode = self.request.query_params.get("mode", "normal")
        if self.action == 'retrieve' or mode == "detailed":
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
    filter_class = LaunchFilter
    search_fields = ('$name', '$rocket__configuration__name', '$rocket__configuration__launch_agency__name',
                     '$rocket__configuration__launch_agency__abbrev', '$mission__name', '$pad__location__name',
                     '$pad__name', '$rocket__spacecraftflight__spacecraft__name')
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
        serial_number = self.request.query_params.get('serial_number',
                                                      None)
        launcher_config__id = self.request.query_params.get(
            'launcher_config__id', None)
        location_filters = self.request.query_params.get('location__ids',
                                                         None)
        lsp_filters = self.request.query_params.get('lsp__ids', None)
        related = self.request.query_params.get('related', None)
        is_crewed = self.request.query_params.get('is_crewed', None)

        now = datetime.datetime.now()
        dayago = now - timedelta(days=1)

        launches = Launch.objects.all().filter(net__gte=dayago)

        if location_filters and lsp_filters:
            lsp_filters = lsp_filters.split(',')
            location_filters = location_filters.split(',')
            launches = launches.filter(Q(
                rocket__configuration__launch_agency__id__in=lsp_filters) | Q(
                pad__location__id__in=location_filters))

        elif lsp_filters:
            lsp_filters = lsp_filters.split(',')
            launches = launches.filter(
                rocket__configuration__launch_agency__id__in=lsp_filters)

        elif location_filters:
            location_filters = location_filters.split(',')
            launches = launches.filter(
                pad__location__id__in=location_filters)

        if ids:
            ids = ids.split(',')
            launches = launches.filter(id__in=ids)

        if serial_number:
            launches = launches.filter(
                rocket__firststage__launcher__serial_number=serial_number)

        if is_crewed:
            if is_crewed == 'true':
                launches = launches.filter(
                    rocket__spacecraftflight__launch_crew__isnull=False)
            elif is_crewed == 'false':
                launches = launches.filter(
                    rocket__spacecraftflight__launch_crew__isnull=True)

        if lsp_name:
            launches = launches.filter(Q(
                rocket__configuration__launch_agency__name__icontains=lsp_name) |
                                       Q(
                                           rocket__configuration__launch_agency__abbrev__icontains=lsp_name))
            if related:
                try:
                    agency = Agency.objects.get(name=lsp_name)
                    related_agency = agency.related_agencies.all()
                    for related in related_agency:
                        related_launches = launches.filter(
                            rocket__configuration__launch_agency__id=related.id)
                        launches = launches | related_launches
                except Agency.DoesNotExist:
                    print("Cant find agency.")

        if lsp_id:
            launches = launches.filter(
                rocket__configuration__launch_agency__id=lsp_id)
            if related:
                try:
                    agency = Agency.objects.get(name=lsp_id)
                    related_agency = agency.related_agencies.all()
                    for related in related_agency:
                        related_launches = launches.filter(
                            rocket__configuration__launch_agency__id=related.id)
                        launches = launches | related_launches
                except Agency.DoesNotExist:
                    print("Cant find agency.")

        if launcher_config__id:
            launches = launches.filter(
                rocket__configuration__id=launcher_config__id)

        launches = launches.select_related(
            'rocket__spacecraftflight').select_related(
            'status').prefetch_related(
            'info_urls').prefetch_related('vid_urls').select_related(
            'rocket').select_related(
            'mission').select_related('pad').select_related(
            'pad__location').prefetch_related(
            'rocket__configuration').prefetch_related(
            'rocket__configuration__launch_agency').prefetch_related(
            'mission__mission_type').prefetch_related(
            'rocket__firststage').select_related(
            'rocket__configuration__launch_agency').order_by(
            'net', 'id').distinct()

        return launches

    def get_serializer_class(self):
        mode = self.request.query_params.get("mode", "normal")
        if self.action == 'retrieve' or mode == "detailed":
            return LaunchDetailedSerializer
        elif mode == "list":
            return LaunchListSerializer
        else:
            return LaunchSerializer

    now = datetime.datetime.now()
    permission_classes = [HasGroupPermission]
    permission_groups = {
        'retrieve': ['_Public'],  # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public']  # list returns None and is therefore NOT accessible by anyone (GET 'site.com/api/foo')
    }
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filter_fields = ('name', 'rocket__configuration__name', 'rocket__configuration__launch_agency__name', 'status',
                     'rocket__spacecraftflight__spacecraft__name',
                     'rocket__spacecraftflight__spacecraft__id',)
    search_fields = ('$name', '$rocket__configuration__name', '$rocket__configuration__launch_agency__name',
                     '$rocket__configuration__launch_agency__abbrev', '$mission__name', '$pad__location__name',
                     '$pad__name', '$rocket__spacecraftflight__spacecraft__name')
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
        location_filters = self.request.query_params.get('location__ids', None)
        lsp_filters = self.request.query_params.get('lsp__ids', None)
        related = self.request.query_params.get('related', None)
        is_crewed = self.request.query_params.get('is_crewed', None)

        now = datetime.datetime.now()

        launches = Launch.objects.all().filter(net__lte=now)

        if location_filters and lsp_filters:
            lsp_filters = lsp_filters.split(',')
            location_filters = location_filters.split(',')
            launches = launches.filter(Q(
                rocket__configuration__launch_agency__id__in=lsp_filters) | Q(
                pad__location__id__in=location_filters))

        elif lsp_filters:
            lsp_filters = lsp_filters.split(',')
            launches = launches.filter(
                rocket__configuration__launch_agency__id__in=lsp_filters)

        elif location_filters:
            location_filters = location_filters.split(',')
            launches = launches.filter(
                pad__location__id__in=location_filters)

        if ids:
            ids = ids.split(',')
            launches = launches.filter(id__in=ids)
        if serial_number:
            launches = launches.filter(rocket__firststage__launcher__serial_number=serial_number)
        if is_crewed:
            if is_crewed == 'true':
                launches = launches.filter(rocket__spacecraftflight__launch_crew__isnull=False)
            elif is_crewed == 'false':
                launches = launches.filter(rocket__spacecraftflight__launch_crew__isnull=True)
        if lsp_name:
            launches = launches.filter(Q(rocket__configuration__launch_agency__name__icontains=lsp_name) |
                                       Q(rocket__configuration__launch_agency__abbrev__icontains=lsp_name))
            if related:
                try:
                    agency = Agency.objects.get(name=lsp_name)
                    related_agency = agency.related_agencies.all()
                    for related in related_agency:
                        related_launches = launches.filter(rocket__configuration__launch_agency__id=related.id)
                        launches = launches | related_launches
                except Agency.DoesNotExist:
                    print("Cant find agency.")
        if lsp_id:
            launches = launches.filter(rocket__configuration__launch_agency__id=lsp_id)
            if related:
                try:
                    agency = Agency.objects.get(name=lsp_id)
                    related_agency = agency.related_agencies.all()
                    for related in related_agency:
                        related_launches = launches.filter(rocket__configuration__launch_agency__id=related.id)
                        launches = launches | related_launches
                except Agency.DoesNotExist:
                    print("Cant find agency.")
        if launcher_config__id:
            launches = launches.filter(rocket__configuration__id=launcher_config__id)

        launches = launches.select_related(
            'rocket__spacecraftflight').select_related(
            'status').prefetch_related(
            'info_urls').prefetch_related('vid_urls').select_related(
            'rocket').select_related(
            'mission').select_related('pad').select_related(
            'pad__location').prefetch_related(
            'rocket__configuration').prefetch_related(
            'rocket__configuration__launch_agency').prefetch_related(
            'mission__mission_type').prefetch_related(
            'rocket__firststage').select_related(
            'rocket__configuration__launch_agency').order_by(
            '-net', 'id').distinct()

        return launches

    def get_serializer_class(self):
        mode = self.request.query_params.get("mode", "normal")
        if self.action == 'retrieve' or mode == "detailed":
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
    filter_fields = ('name', 'rocket__configuration__name', 'rocket__configuration__launch_agency__name', 'status',
                     'rocket__spacecraftflight__spacecraft__name',
                     'rocket__spacecraftflight__spacecraft__id',)
    search_fields = ('$name', '$rocket__configuration__name', '$rocket__configuration__launch_agency__name',
                     '$rocket__configuration__launch_agency__abbrev', '$mission__name', '$pad__location__name',
                     '$pad__name', '$rocket__spacecraftflight__spacecraft__name')
    ordering_fields = ('id', 'name', 'net',)
