from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from api.models import *
from api.permission import HasGroupPermission


from api.v340.config.spacecraft.serializers import SpacecraftConfigurationSerializer, SpacecraftConfigurationDetailSerializer


class SpacecraftConfigViewSet(ModelViewSet):
    """
    API endpoint that allows Spacecraft Configs to be viewed.

    GET:
    Return a list of all the existing spacecraft.

    FILTERS:
    Parameters - 'name', 'launch_agency', 'in_use', 'human_rated'
    Example - /api/3.3.0/config/spacecraft/?status=Active

    SEARCH EXAMPLE:
    Example - /api/3.3.0/config/spacecraft/?search=Dragon

    ORDERING:
    Fields - 'name', 'launch_mass', 'leo_capacity', 'gto_capacity', 'launch_cost'
    Example - /api/3.3.0/config/spacecraft/?order=launch_mass

    """
    def get_serializer_class(self):
        mode = self.request.query_params.get("mode", "normal")
        if self.action == 'retrieve' or mode == "detailed":
            return SpacecraftConfigurationDetailSerializer
        else:
            return SpacecraftConfigurationSerializer

    queryset = SpacecraftConfiguration.objects.all()
    permission_classes = [HasGroupPermission]
    permission_groups = {
        'retrieve': ['_Public'],  # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public']  # list returns None and is therefore NOT accessible by anyone (GET 'site.com/api/foo')
    }
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filter_fields = ('name', 'launch_agency', 'in_use', 'human_rated')
    search_fields = ('name', 'launch_agency__name',)
    ordering_fields = ('name', 'launch_mass', 'leo_capacity', 'gto_capacity', 'launch_cost')