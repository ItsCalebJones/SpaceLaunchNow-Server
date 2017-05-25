# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render


# Create your views here.
from rest_framework import viewsets, permissions

from bot.models import Launch, Notification
from bot.serializer import LaunchSerializer, NotificationSerializer


class LaunchViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Launcher to be viewed or edited.
    """
    queryset = Launch.objects.all()
    serializer_class = LaunchSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class NotificationViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Launcher to be viewed or edited.
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
