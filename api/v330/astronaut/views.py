from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from api.models import *
from api.permission import HasGroupPermission
from api.v330.astronaut.filters import AstronautsFilter
from api.v330.astronaut.serializers import AstronautDetailedSerializer, AstronautListSerializer, \
    AstronautNormalSerializer, AstronautDetailedWithLaunchListSerializer


class AstronautViewSet(ModelViewSet):
    """
    API endpoint that allows Astronauts to be viewed.

    GET:
    Return a list of all the existing astronauts.

    MODE:
    Normal, List and Detailed
    /3.3.0/astronaut/?mode=detailed

    FILTERS:
    Parameters - 'name', 'status', 'nationality', 'agency__name', 'agency__abbrev', 'date_of_birth', 'date_of_death', 'status_ids'
    Example - /3.3.0/astronaut/?nationality=American

    SEARCH EXAMPLE:
    /3.3.0/astronaut/?search=armstrong
    Searches through name, nationality and agency name

    ORDERING:
    Fields - 'name', 'status'
    Example - /3.3.0/astronaut/?order=name

    """
    def get_queryset(self):
        ids = self.request.query_params.get('status_ids', None)
        if ids:
            ids = ids.split(',')
            return Astronauts.objects.filter(status_id__in=ids)
        else:
            return Astronauts.objects.all()
    queryset = Astronauts.objects.all()
    permission_classes = [HasGroupPermission]
    permission_groups = {
        'retrieve': ['_Public'], # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public'] # list returns None and is therefore NOT accessible by anyone (GET 'site.com/api/foo')
    }

    def get_serializer_class(self):
        mode = self.request.query_params.get("mode", "normal")
        if mode == "launch_list" and self.action == 'retrieve':
            return AstronautDetailedWithLaunchListSerializer
        elif mode == "detailed" or self.action == 'retrieve':
            return AstronautDetailedSerializer
        elif mode == "list":
            return AstronautListSerializer
        else:
            return AstronautNormalSerializer

    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filter_class = AstronautsFilter
    search_fields = ('$name', 'nationality', 'agency__name', 'agency__abbrev')
    ordering_fields = ('name', 'status', )
