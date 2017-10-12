# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render


# Create your views here.
from bot.libraries.launchlibrarysdk import LaunchLibrarySDK
from bot.utils.deserializer import launch_json_to_model


def index(request):
    return render(request, 'landing/index.html',)


# Create your views here.
def next_launch(request):
    launchLibrary = LaunchLibrarySDK(version='1.2.1')
    response = launchLibrary.get_next_launch()
    if response.status_code is 200:
        response_json = response.json()
        launch_data = response_json['launches']
        launch = launch_json_to_model(launch_data[0])
        return render(request, 'next/next.html', {'launch': launch})
    else:
        return render(request, 'next/next.html', )
