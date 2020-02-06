from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from api.models import *
from api.permission import HasGroupPermission
from api.v350.astronaut.filters import AstronautsFilter
from api.v350.astronaut.serializers import AstronautDetailedSerializer, AstronautListSerializer, \
    AstronautNormalSerializer


class AstronautViewSet(ModelViewSet):
    """
    API endpoint that allows Astronaut to be viewed.

    GET:
    Return a list of all the existing astronauts.

    MODE:
    Normal, List and Detailed
    /3.5.0/astronaut/?mode=detailed

    FILTERS:
    Parameters - 'name', 'status', 'nationality', 'agency__name', 'agency__abbrev', 'date_of_birth',
     'date_of_death', 'status_ids'
    Example - /3.5.0/astronaut/?nationality=American

    SEARCH EXAMPLE:
    /3.5.0/astronaut/?search=armstrong
    Searches through name, nationality and agency name

    ORDERING:
    Fields - 'name', 'status', 'date_of_birth'
    Example - /3.5.0/astronaut/?order=name

    """
    def get_queryset(self):
        ids = self.request.query_params.get('status_ids', None)
        agency_ids = self.request.query_params.get('agency_ids', None)
        has_flown = self.request.query_params.get('has_flown', None)

        astros = Astronaut.objects.all()

        if has_flown:
            if has_flown == 'true':
                astros = astros.filter(astronautflight__isnull=False).distinct()
            elif has_flown == 'false':
                astros = astros.filter(astronautflight__isnull=True).distinct()

        if agency_ids:
            agency_ids = agency_ids.split(',')
            astros = astros.filter(agency_id__in=agency_ids).distinct()

        if ids:
            ids = ids.split(',')
            astros = astros.filter(status_id__in=ids).distinct()

        return astros

    queryset = Astronaut.objects.all()
    permission_classes = [HasGroupPermission]
    permission_groups = {
        'retrieve': ['_Public'],
        'list': ['_Public']
    }

    def get_serializer_class(self):
        mode = self.request.query_params.get("mode", "normal")
        if mode == "detailed" or self.action == 'retrieve':
            return AstronautDetailedSerializer
        elif mode == "list":
            return AstronautListSerializer
        else:
            return AstronautNormalSerializer

    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filter_class = AstronautsFilter
    search_fields = ('$name', 'nationality', 'agency__name', 'agency__abbrev')
    ordering_fields = ('name', 'status', 'date_of_birth')
    http_method_names = ['get']
