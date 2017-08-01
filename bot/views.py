# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render


# Create your views here.
from rest_framework import viewsets, permissions

from bot.models import Launch, Notification, DailyDigestRecord
from bot.serializer import LaunchSerializer, NotificationSerializer, DailyDigestRecordSerializer


class LaunchViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Launcher to be viewed or edited.
    """
    queryset = Launch.objects.all()
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_serializer_class(self):
        if self.request.version == 'v1':
            return LaunchSerializer
        return LaunchSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Launcher to be viewed or edited.
    """
    queryset = Notification.objects.all()
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_serializer_class(self):
        if self.request.version == 'v1':
            return NotificationSerializer
        return NotificationSerializer


class DailyDigestRecordViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Records to be viewed or edited.
    """
    queryset = DailyDigestRecord.objects.all()
    serializer_class = DailyDigestRecordSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_serializer_class(self):
        if self.request.version == 'v1':
            return DailyDigestRecordSerializer
        return DailyDigestRecordSerializer
