from api.models import Launcher, LauncherDetail, Orbiter

from api.serializers import OrbiterSerializer, LauncherSerializer, LauncherDetailSerializer
from rest_framework import viewsets
from rest_framework import permissions


class LauncherViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Launcher to be viewed or edited.
    """
    queryset = Launcher.objects.all()
    serializer_class = LauncherSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class LauncherDetailViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = LauncherDetail.objects.all()
    serializer_class = LauncherDetailSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class OrbiterViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Orbiter.objects.all()
    serializer_class = OrbiterSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)