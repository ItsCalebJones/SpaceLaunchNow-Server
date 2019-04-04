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

        launches = Launch.objects.all()

        if location_filters and lsp_filters:
            lsp_filters = lsp_filters.split(',')
            location_filters = location_filters.split(',')
            launches = launches.filter(Q(rocket__configuration__launch_agency__id__in=lsp_filters) | Q(
                pad__location__id__in=location_filters))
        if lsp_filters:
            lsp_filters = lsp_filters.split(',')
            launches = launches.filter(rocket__configuration__launch_agency__id__in=lsp_filters)

        if location_filters:
            location_filters = location_filters.split(',')
            launches = launches.filter(pad__location__id__in=location_filters)
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

            return total_launches.order_by('net', 'id')
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
            return total_launches.order_by('net', 'id')
        if launcher_config__id:
            launches = launches.filter(rocket__configuration__id=launcher_config__id)

        launches = launches.order_by('net', 'id').distinct()

        return launches

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
        serial_number = self.request.query_params.get('serial_number', None)
        launcher_config__id = self.request.query_params.get('launcher_config__id', None)
        related = self.request.query_params.get('related', None)
        is_crewed = self.request.query_params.get('is_crewed', None)

        now = datetime.datetime.now()
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
                'rocket__configuration__launch_agency').order_by('net', 'id')
        if lsp_filters:
            lsp_filters = lsp_filters.split(',')
            return Launch.objects.filter(net__gte=now).filter(rocket__configuration__launch_agency__id__in=lsp_filters).prefetch_related(
                'info_urls').prefetch_related('vid_urls').select_related('rocket').select_related(
                'mission').select_related('pad').select_related('pad__location').prefetch_related(
                'rocket__configuration').prefetch_related('rocket__configuration__launch_agency').prefetch_related(
                'mission__mission_type').prefetch_related('rocket__firststage').select_related(
                'rocket__configuration__launch_agency').order_by('net', 'id')

        if location_filters:
            location_filters = location_filters.split(',')
            return Launch.objects.filter(net__gte=now).filter(pad__location__id__in=location_filters).prefetch_related(
                'info_urls').prefetch_related('vid_urls').select_related('rocket').select_related(
                'mission').select_related('pad').select_related('pad__location').prefetch_related(
                'rocket__configuration').prefetch_related('rocket__configuration__launch_agency').prefetch_related(
                'mission__mission_type').prefetch_related('rocket__firststage').select_related(
                'rocket__configuration__launch_agency').order_by('net', 'id')

        if ids:
            ids = ids.split(',')
            return Launch.objects.filter(net__gte=now).filter(id__in=ids).prefetch_related(
                'info_urls').prefetch_related('vid_urls').select_related('rocket').select_related(
                'mission').select_related('pad').select_related('pad__location').prefetch_related(
                'rocket__configuration').prefetch_related('rocket__configuration__launch_agency').prefetch_related(
                'mission__mission_type').prefetch_related('rocket__firststage').select_related(
                'rocket__configuration__launch_agency').order_by('net', 'id')
        if serial_number:
            return Launch.objects.filter(
                net__gte=now).filter(rocket__firststage__launcher__serial_number=serial_number).prefetch_related(
                'info_urls').prefetch_related('vid_urls').select_related('rocket').select_related(
                'mission').select_related('pad').select_related('pad__location').prefetch_related(
                'rocket__configuration').prefetch_related('rocket__configuration__launch_agency').prefetch_related(
                'mission__mission_type').prefetch_related('rocket__firststage').select_related(
                'rocket__configuration__launch_agency').order_by('net', 'id')
        if is_crewed:
            if is_crewed == 'true':
                return Launch.objects.filter(net__gte=now).filter(
                    rocket__spacecraftflight__launch_crew__isnull=False).prefetch_related(
                    'info_urls').prefetch_related('vid_urls').select_related(
                    'rocket').select_related(
                    'mission').select_related('pad').select_related(
                    'pad__location').prefetch_related(
                    'rocket__configuration').prefetch_related(
                    'rocket__configuration__launch_agency').prefetch_related(
                    'mission__mission_type').prefetch_related(
                    'rocket__firststage').select_related(
                    'rocket__configuration__launch_agency').order_by(
                    'net', 'id')
            elif is_crewed == 'false':
                return Launch.objects.filter(net__gte=now).filter(
                    rocket__spacecraftflight__launch_crew__isnull=True).prefetch_related(
                    'info_urls').prefetch_related('vid_urls').select_related(
                    'rocket').select_related(
                    'mission').select_related('pad').select_related(
                    'pad__location').prefetch_related(
                    'rocket__configuration').prefetch_related(
                    'rocket__configuration__launch_agency').prefetch_related(
                    'mission__mission_type').prefetch_related(
                    'rocket__firststage').select_related(
                    'rocket__configuration__launch_agency').order_by(
                    'net', 'id')
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
            return total_launches.order_by('net', 'id')
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
            return total_launches.order_by('net', 'id')
        if launcher_config__id:
            return Launch.objects.filter(net__gte=now).filter(
                rocket__configuration__id=launcher_config__id).prefetch_related(
                'info_urls').prefetch_related('vid_urls').select_related('rocket').select_related(
                'mission').select_related('pad').select_related('pad__location').prefetch_related(
                'rocket__configuration').prefetch_related('rocket__configuration__launch_agency').prefetch_related(
                'mission__mission_type').prefetch_related('rocket__firststage').select_related(
                'rocket__configuration__launch_agency').order_by('net', 'id')

        else:
            return Launch.objects.filter(net__gte=now).prefetch_related(
                'info_urls').prefetch_related('vid_urls').select_related('rocket').select_related(
                'mission').select_related('pad').select_related('pad__location').prefetch_related(
                'rocket__configuration').prefetch_related('rocket__configuration__launch_agency').prefetch_related(
                'mission__mission_type').prefetch_related('rocket__firststage').select_related(
                'rocket__configuration__launch_agency').order_by('net', 'id').all()

    def get_serializer_class(self):
        mode = self.request.query_params.get("mode", "normal")
        if mode == "detailed":
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
    filter_fields = ('name', 'rocket__configuration__name', 'rocket__configuration__launch_agency__name', 'status', 'rocket__spacecraftflight__spacecraft__name')
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
        related = self.request.query_params.get('related', None)
        location_filters = self.request.query_params.get('location__ids', None)
        lsp_filters = self.request.query_params.get('lsp__ids', None)
        is_crewed = self.request.query_params.get('is_crewed', None)

        now = datetime.datetime.now()

        if location_filters and lsp_filters:
            lsp_filters = lsp_filters.split(',')
            location_filters = location_filters.split(',')
            return Launch.objects.filter(net__lte=now).filter(Q(rocket__configuration__launch_agency__id__in=lsp_filters) | Q(
                pad__location__id__in=location_filters)).prefetch_related(
                'info_urls').prefetch_related('vid_urls').select_related('rocket').select_related(
                'mission').select_related('pad').select_related('pad__location').prefetch_related(
                'rocket__configuration').prefetch_related('rocket__configuration__launch_agency').prefetch_related(
                'mission__mission_type').prefetch_related('rocket__firststage').select_related(
                'rocket__configuration__launch_agency').order_by('-net', 'id')
        if lsp_filters:
            lsp_filters = lsp_filters.split(',')
            return Launch.objects.filter(net__lte=now).filter(rocket__configuration__launch_agency__id__in=lsp_filters).prefetch_related(
                'info_urls').prefetch_related('vid_urls').select_related('rocket').select_related(
                'mission').select_related('pad').select_related('pad__location').prefetch_related(
                'rocket__configuration').prefetch_related('rocket__configuration__launch_agency').prefetch_related(
                'mission__mission_type').prefetch_related('rocket__firststage').select_related(
                'rocket__configuration__launch_agency').order_by('-net', 'id')

        if location_filters:
            location_filters = location_filters.split(',')
            return Launch.objects.filter(net__lte=now).filter(pad__location__id__in=location_filters).prefetch_related(
                'info_urls').prefetch_related('vid_urls').select_related('rocket').select_related(
                'mission').select_related('pad').select_related('pad__location').prefetch_related(
                'rocket__configuration').prefetch_related('rocket__configuration__launch_agency').prefetch_related(
                'mission__mission_type').prefetch_related('rocket__firststage').select_related(
                'rocket__configuration__launch_agency').order_by('-net', 'id')
        if ids:
            ids = ids.split(',')
            return Launch.objects.filter(id__in=ids).filter(net__lte=now).order_by('-net', 'id')
        if serial_number:
            return Launch.objects.filter(rocket__firststage__launcher__serial_number=serial_number).filter(
                net__lte=now).order_by('-net', 'id')
        if is_crewed:
            if is_crewed == 'true':
                return Launch.objects.filter(net__lte=now).filter(
                    rocket__spacecraftflight__launch_crew__isnull=False).prefetch_related(
                    'info_urls').prefetch_related('vid_urls').select_related(
                    'rocket').select_related(
                    'mission').select_related('pad').select_related(
                    'pad__location').prefetch_related(
                    'rocket__configuration').prefetch_related(
                    'rocket__configuration__launch_agency').prefetch_related(
                    'mission__mission_type').prefetch_related(
                    'rocket__firststage').select_related(
                    'rocket__configuration__launch_agency').order_by(
                    '-net', 'id')
            elif is_crewed == 'false':
                return Launch.objects.filter(net__lte=now).filter(
                    rocket__spacecraftflight__launch_crew__isnull=True).prefetch_related(
                    'info_urls').prefetch_related('vid_urls').select_related(
                    'rocket').select_related(
                    'mission').select_related('pad').select_related(
                    'pad__location').prefetch_related(
                    'rocket__configuration').prefetch_related(
                    'rocket__configuration__launch_agency').prefetch_related(
                    'mission__mission_type').prefetch_related(
                    'rocket__firststage').select_related(
                    'rocket__configuration__launch_agency').order_by(
                    '-net', 'id')
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
            return total_launches.order_by('-net', 'id')
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
            return total_launches.order_by('-net', 'id')
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
                'rocket__configuration__launch_agency').order_by('-net', 'id').all()

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
    filter_fields = ('name', 'rocket__configuration__name', 'rocket__configuration__launch_agency__name', 'status', 'rocket__spacecraftflight__spacecraft__name')
    search_fields = ('$name', '$rocket__configuration__name', '$rocket__configuration__launch_agency__name',
                     '$rocket__configuration__launch_agency__abbrev', '$mission__name', '$pad__location__name',
                     '$pad__name', '$rocket__spacecraftflight__spacecraft__name')
    ordering_fields = ('id', 'name', 'net',)
