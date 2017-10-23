# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http import Http404
from django.shortcuts import render


# Create your views here.
from bot.libraries.launchlibrarysdk import LaunchLibrarySDK
from bot.utils.deserializer import launch_json_to_model


def index(request):
    return render(request, 'web/index.html',)


# Create your views here.
def next_launch(request):
    youtube_urls = []
    launchLibrary = LaunchLibrarySDK(version='1.2.2')
    response = launchLibrary.get_next_launch()
    if response.status_code is 200:
        response_json = response.json()
        launch_data = response_json['launches']
        launch = launch_json_to_model(launch_data[0])
        _vids = launch.vid_urls.all()
        for url in _vids:
            if 'youtube' in url.vid_url:
                youtube_urls.append(url.vid_url)
        return render(request, 'web/launch_page.html', {'launch': launch, 'youtube_urls': youtube_urls})
    else:
        return render(request, 'web/launch_page.html', )


# Create your views here.
def launch_by_id(request, pk):
    youtube_urls = []
    launchLibrary = LaunchLibrarySDK(version='1.2.1')
    response = launchLibrary.get_launch_by_id(pk)
    if response.status_code is 200:
        response_json = response.json()
        launch_data = response_json['launches']
        launch = launch_json_to_model(launch_data[0])
        _vids = launch.vid_urls.all()
        for url in _vids:
            if 'youtube' in url.vid_url:
                youtube_urls.append(url.vid_url)
        return render(request, 'web/launch_page.html', {'launch': launch, 'youtube_urls': youtube_urls})
    else:
        raise Http404


# Create your views here.
def launches(request,):
    launchLibrary = LaunchLibrarySDK()
    query = request.GET.get('q')
    if query is not None:
        response = launchLibrary.get_next_launch(count=5)
    else:
        response = launchLibrary.get_next_launch(count=5)
    if response.status_code is 200:
        response_json = response.json()
        launch_data = response_json['launches']
        _launches = []
        for launch in launch_data:
            launch = launch_json_to_model(launch)
            launch.save()
            _launches.append(launch)
        return render(request, 'web/launches.html', {'launches': _launches})
    else:
        raise Http404
