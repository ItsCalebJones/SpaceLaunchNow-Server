from rest_framework.viewsets import ModelViewSet
from api.models import *
from api.permission import HasGroupPermission
import pytz

from api.v330.events.serializers import EventsSerializer


class EventViewSet(ModelViewSet):
    """
    API endpoint that allows future Events to be viewed.

    GET:
    Return a list of future Events
    """
    now = datetime.datetime.now(tz=pytz.utc)
    queryset = Events.objects.filter(date__gte=now)
    serializer_class = EventsSerializer
    permission_classes = [HasGroupPermission]
    permission_groups = {

        'retrieve': ['_Public'],  # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        'list': ['_Public']  # list returns None and is therefore NOT accessible by anyone (GET 'site.com/api/foo')
    }