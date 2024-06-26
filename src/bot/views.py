# Create your views here.
from rest_framework import viewsets

from bot.models import DailyDigestRecord, LaunchNotificationRecord
from bot.permission import HasGroupPermission
from bot.serializer import DailyDigestRecordSerializer, NotificationSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Launcher to be viewed or edited.
    """

    queryset = LaunchNotificationRecord.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [HasGroupPermission]
    permission_groups = {
        "create": ["Developers"],  # Developers can POST
        "partial_update": ["Developers"],  # Designers and Developers can PATCH
        "retrieve": ["Contributors"],  # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        "list": ["Contributors"],
    }


class DailyDigestRecordViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Records to be viewed or edited.
    """

    queryset = DailyDigestRecord.objects.all()
    serializer_class = DailyDigestRecordSerializer
    permission_classes = [HasGroupPermission]
    permission_groups = {
        "create": ["Developers"],  # Developers can POST
        "partial_update": ["Developers"],  # Designers and Developers can PATCH
        "retrieve": ["Contributors"],  # retrieve can be accessed without credentials (GET 'site.com/api/foo/1')
        "list": ["Contributors"],
    }
