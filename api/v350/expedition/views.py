from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from api.models import *
from api.permission import HasGroupPermission
from api.v350.expedition.filters import ExpeditionFilter

from api.v350.expedition.serializers import ExpeditionDetailSerializer, ExpeditionSerializer


class ExpeditionViewSet(ModelViewSet):
    """
    API endpoint that allows Expeditions to be viewed.

    GET:
    Return a list of all the existing expeditions.

    MODE:
    Normal and Detailed
    /api/3.5.0/expedition/?mode=detailed

    FILTERS:
    Fields - 'name', 'crew__astronaut', 'crew__astronaut__agency', 'space_station'

    Get all Expeditions with the Space Station ID of 1.
    Example - /api/3.5.0/expedition/?space_station=1&mode=detailed

    Search for all Expeditions with the Astronaut named John
    Example - /api/3.5.0/expedition/?search=John

    ORDERING:
    Fields - 'id', 'start', 'end'
    Order reverse via Start date.
    Example - /3.5.0/astronaut/?order=-start
    """
    def get_serializer_class(self):
        mode = self.request.query_params.get("mode", "normal")
        if self.action == 'retrieve' or mode == "detailed":
            return ExpeditionDetailSerializer
        else:
            return ExpeditionSerializer

    queryset = Expedition.objects.all().prefetch_related(
        'space_station').prefetch_related(
        'space_station__status').prefetch_related(
        'space_station__orbit')
    permission_classes = [HasGroupPermission]
    permission_groups = {
        'retrieve': ['_Public'],  # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public']  # list returns None and is therefore NOT accessible by anyone (GET 'site.com/api/foo')
    }
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filter_class = ExpeditionFilter
    search_fields = ('^name', '^crew__astronaut__name', '^crew__astronaut__agency__name',
                     '^crew__astronaut__agency__abbrev', '^crew__astronaut__nationality')
    ordering_fields = ('id', 'start', 'end',)
    http_method_names = ['get']