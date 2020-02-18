from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.viewsets import ModelViewSet
from api.models import *
from api.permission import HasGroupPermission
from datetime import datetime, timedelta

from api.v350.events.serializers import EventsSerializer


class UpcomingEventViewSet(ModelViewSet):
    """
    API endpoint that allows future Events to be viewed.

    GET:
    Return a list of future Events
    """

    def get_queryset(self):
        now = datetime.now()
        now = now - timedelta(days=1)
        return Events.objects.filter(date__gte=now).order_by('date', 'id')

    serializer_class = EventsSerializer
    permission_classes = [HasGroupPermission]
    permission_groups = {
        'retrieve': ['_Public'],  # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public']  # list returns None and is therefore NOT accessible by anyone (GET 'site.com/api/foo')
    }
    filter_backends = (DjangoFilterBackend, SearchFilter)
    search_fields = ('name',)
    http_method_names = ['get']


class PreviousEventViewSet(ModelViewSet):
    """
    API endpoint that allows past Events to be viewed.

    GET:
    Return a list of past Events
    """

    def get_queryset(self):
        now = datetime.now()
        return Events.objects.filter(date__lte=now).order_by('-date', 'id')

    serializer_class = EventsSerializer
    permission_classes = [HasGroupPermission]
    permission_groups = {

        'retrieve': ['_Public'],  # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public']  # list returns None and is therefore NOT accessible by anyone (GET 'site.com/api/foo')
    }
    filter_backends = (DjangoFilterBackend, SearchFilter)
    search_fields = ('name',)
    http_method_names = ['get']


class EventViewSet(ModelViewSet):
    """
    API endpoint that allows all Events to be viewed.

    GET:
    Return a list of all Events

    SEARCH EXAMPLE:
    /3.5.0/event/?search=Dragon
    Searches through name
    """
    queryset = Events.objects.all().prefetch_related(
        'launch__mission').prefetch_related(
        'launch__rocket').prefetch_related(
        'launch').prefetch_related(
        'news__events__type').prefetch_related(
        'launch__status').select_related(
        'type').prefetch_related('launch__launch_service_provider')
    serializer_class = EventsSerializer
    permission_classes = [HasGroupPermission]
    permission_groups = {

        'retrieve': ['_Public'],  # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public']  # list returns None and is therefore NOT accessible by anyone (GET 'site.com/api/foo')
    }
    filter_backends = (DjangoFilterBackend, SearchFilter)
    search_fields = ('name',)
    http_method_names = ['get']