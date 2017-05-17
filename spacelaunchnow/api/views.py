from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from spacelaunchnow.api.serializers import OrbiterSerializer, LauncherSerializer, LauncherDetailSerializer


class LauncherViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = LauncherSerializer


class LauncherDetailViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = LauncherDetailSerializer


class OrbiterViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = OrbiterSerializer
