from itertools import chain

from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter

from api.v310.serializers import *
from datetime import datetime, timedelta
from api.models import LauncherConfig, Orbiter, Agency
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
    Parameters - 'featured', 'launch_library_id', 'detailed'
    Example - /3.1.0/agencies/?featured=true&launch_library_id=44&detailed

    SEARCH EXAMPLE:
    /3.1.0/agencies/?search=nasa

    ORDERING:
    Fields - 'id', 'name', 'featured', 'launch_library_id'
    Example - /3.1.0/agencies/?ordering=featured

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
    Example - /3.1.0/launcher_config/?launch_agency__launch_library_id=44

    Get all Launchers with the Agency with name NASA.
    Example - /3.1.0/launcher_config/?launch_agency__name=NASA
    """
    queryset = LauncherConfig.objects.all()
    serializer_class = LauncherConfigDetailSerializer
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


class LauncherViewSet(ModelViewSet):
    """
    API endpoint that allows Launcher instances to be viewed.

    GET:
    Return a list of all the existing launcher instances.

    FILTERS:

    Get all Launchers with the Launch Library ID of 44.
    Example - /3.1.0/launcher

    Get all Launchers with the Agency with name NASA.
    Example - /3.1.0/launcher/?launch_agency__name=NASA
    """
    queryset = Launcher.objects.all()
    serializer_class = LauncherDetailedSerializer
    permission_classes = [HasGroupPermission]
    permission_groups = {
        'create': ['Developers'],  # Developers can POST
        'destroy': ['Developers'],  # Developers can POST
        'partial_update': ['Contributors', 'Developers'],  # Designers and Developers can PATCH
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
    queryset = Orbiter.objects.all()
    serializer_class = OrbiterDetailSerializer
    permission_classes = [HasGroupPermission]
    permission_groups = {
        'create': ['Developers'],  # Developers can POST
        'destroy': ['Developers'],  # Developers can POST
        'partial_update': ['Contributors', 'Developers'],  # Designers and Developers can PATCH
        'retrieve': ['_Public'],  # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public']  # list returns None and is therefore NOT accessible by anyone (GET 'site.com/api/foo')
    }


class EventViewSet(ModelViewSet):
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


class LaunchViewSet(ModelViewSet):
    """
    API endpoint that returns all Launch objects.

    GET:
    Return a list of all Launch objects.
    """

    def get_queryset(self):
        ids = self.request.query_params.get('id', None)
        lsp_name = self.request.query_params.get('lsp__name', None)
        lsp_id = self.request.query_params.get('lsp__id', None)
        if ids:
            ids = ids.split(',')
            return Launch.objects.filter(id__in=ids).order_by('net')
        if lsp_name:
            launches = Launch.objects.filter(lsp__name=lsp_name)
            total_launches = launches
            try:
                agency = Agency.objects.get(name=lsp_name)
                related_agency = agency.related_agencies.all()
                for related in related_agency:
                    related_launches = Launch.objects.filter(lsp__id=related.id)
                    total_launches = launches | related_launches
            except Agency.DoesNotExist:
                print ("Cant find agency.")
            return total_launches.order_by('net')
        if lsp_id:
            launches = Launch.objects.filter(lsp__id=lsp_id)
            total_launches = launches
            try:
                agency = Agency.objects.get(name=lsp_id)
                related_agency = agency.related_agencies.all()
                for related in related_agency:
                    related_launches = Launch.objects.filter(lsp__id=related.id)
                    total_launches = launches | related_launches
            except Agency.DoesNotExist:
                print ("Cant find agency.")
            return total_launches.order_by('net')
        else:
            return Launch.objects.order_by('net').prefetch_related('info_urls').prefetch_related(
                'vid_urls').prefetch_related('launcher_config__launch_agency').prefetch_related(
                'pad__location').select_related('mission').select_related('lsp').select_related(
                'launcher_config').select_related('pad').all()

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
        'create': ['Developers'],  # Developers can POST
        'destroy': ['Developers'],  # Developers can POST
        'partial_update': ['Contributors', 'Developers'],  # Designers and Developers can PATCH
        'retrieve': ['_Public'],  # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public']  # list returns None and is therefore NOT accessible by anyone (GET 'site.com/api/foo')
    }
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filter_fields = ('name', 'launcher_config__name', 'lsp__name', 'lsp__id', 'status', 'tbddate', 'tbdtime', 'launcher_config__id', 'launcher__id')
    search_fields = ('$name', '$launcher_config__name', '$lsp__name')
    ordering_fields = ('id', 'name', 'net',)


class UpcomingLaunchViewSet(ModelViewSet):
    """
    API endpoint that returns future Launch objects.

    GET:
    Return a list of future Launches
    """

    def get_queryset(self):
        ids = self.request.query_params.get('id', None)
        lsp_name = self.request.query_params.get('lsp__name', None)
        lsp_id = self.request.query_params.get('lsp__id', None)
        now = datetime.now()
        now = now - timedelta(days=1)
        if ids:
            ids = ids.split(',')
            return Launch.objects.filter(id__in=ids).filter(net__gte=now).order_by('net')
        if lsp_name:
            launches = Launch.objects.filter(lsp__name=lsp_name).filter(net__gte=now)
            total_launches = launches
            try:
                agency = Agency.objects.get(name=lsp_name)
                related_agency = agency.related_agencies.all()
                for related in related_agency:
                    related_launches = Launch.objects.filter(lsp__id=related.id).filter(net__gte=now)
                    total_launches = launches | related_launches
            except Agency.DoesNotExist:
                print ("Cant find agency.")
            return total_launches.order_by('net')
        if lsp_id:
            launches = Launch.objects.filter(lsp__id=lsp_id).filter(net__gte=now)
            total_launches = launches
            try:
                agency = Agency.objects.get(name=lsp_id)
                related_agency = agency.related_agencies.all()
                for related in related_agency:
                    related_launches = Launch.objects.filter(lsp__id=related.id).filter(net__gte=now)
                    total_launches = launches | related_launches
            except Agency.DoesNotExist:
                print ("Cant find agency.")
            return total_launches.order_by('net')
        else:
            return Launch.objects.filter(net__gte=now).prefetch_related('info_urls').prefetch_related(
                'vid_urls').prefetch_related('launcher_config__launch_agency').prefetch_related(
                'pad__location').select_related('mission').select_related('lsp').select_related(
                'launcher_config').select_related('pad').order_by('net').all()

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
        'create': ['Developers'],  # Developers can POST
        'destroy': ['Developers'],  # Developers can POST
        'partial_update': ['Contributors', 'Developers'],  # Designers and Developers can PATCH
        'retrieve': ['_Public'],  # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public']  # list returns None and is therefore NOT accessible by anyone (GET 'site.com/api/foo')
    }
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filter_fields = ('name', 'launcher_config__name', 'status', 'tbddate', 'tbdtime', 'launcher_config__id', 'launcher__id')
    search_fields = ('$name', '$launcher_config__name', '$lsp__name')
    ordering_fields = ('id', 'name', 'net',)


class PreviousLaunchViewSet(ModelViewSet):
    """
    API endpoint that returns previous Launch objects.

    GET:
    Return a list of previous Launches
    """

    def get_queryset(self):
        ids = self.request.query_params.get('id', None)
        lsp_name = self.request.query_params.get('lsp__name', None)
        lsp_id = self.request.query_params.get('lsp__id', None)
        now = datetime.now()
        if ids:
            ids = ids.split(',')
            return Launch.objects.filter(id__in=ids).filter(net__lte=now).order_by('-net')
        if lsp_name:
            launches = Launch.objects.filter(lsp__name=lsp_name).filter(net__lte=now)
            total_launches = launches
            try:
                agency = Agency.objects.get(name=lsp_name)
                related_agency = agency.related_agencies.all()
                for related in related_agency:
                    related_launches = Launch.objects.filter(lsp__id=related.id).filter(net__lte=now)
                    total_launches = launches | related_launches
            except Agency.DoesNotExist:
                print ("Cant find agency.")
            return total_launches.order_by('-net')
        if lsp_id:
            launches = Launch.objects.filter(lsp__id=lsp_id).filter(net__lte=now)
            total_launches = launches
            try:
                agency = Agency.objects.get(id=lsp_id)
                related_agency = agency.related_agencies.all()
                for related in related_agency:
                    related_launches = Launch.objects.filter(lsp__id=related.id).filter(net__lte=now)
                    total_launches = launches | related_launches
            except Agency.DoesNotExist:
                print ("Cant find agency.")
            return total_launches.order_by('-net')
        else:
            return Launch.objects.filter(net__lte=now).prefetch_related('info_urls').prefetch_related(
                'vid_urls').prefetch_related('launcher_config__launch_agency').prefetch_related(
                'pad__location').select_related('mission').select_related('lsp').select_related(
                'launcher_config').select_related('pad').order_by('-net').all()

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
        'create': ['Developers'],  # Developers can POST
        'destroy': ['Developers'],  # Developers can POST
        'partial_update': ['Contributors', 'Developers'],  # Designers and Developers can PATCH
        'retrieve': ['_Public'],  # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public']  # list returns None and is therefore NOT accessible by anyone (GET 'site.com/api/foo')
    }
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filter_fields = ('name', 'launcher_config__name', 'status', 'tbddate', 'tbdtime', 'launcher_config__id', 'launcher__id')
    search_fields = ('$name', '$launcher_config__name', '$lsp__name')
    ordering_fields = ('id', 'name', 'net',)
