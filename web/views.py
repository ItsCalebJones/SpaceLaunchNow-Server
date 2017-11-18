# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http import Http404, HttpResponseNotFound
from django.shortcuts import render, redirect

# Create your views here.
from bot.libraries.launchlibrarysdk import LaunchLibrarySDK
from bot.utils.deserializer import launch_json_to_model


def index(request):
    return render(request, 'web/index.html',)


# Create your views here.
def next_launch(request):
    launchLibrary = LaunchLibrarySDK()
    response = launchLibrary.get_next_launch()
    if response.status_code is 200:
        response_json = response.json()
        launch_data = response_json['launches']
        launch = launch_json_to_model(launch_data[0])
        return redirect('launch_by_id', pk=launch.id)
    else:
        return redirect('launches')


# Create your views here.
def launch_by_id(request, pk, launch=None):
    if launch is not None:
        return create_launch_view(request, launch)
    else:
        launchLibrary = LaunchLibrarySDK()
        response = launchLibrary.get_launch_by_id(pk)
        if response.status_code is 200:
            response_json = response.json()
            launch_data = response_json['launches']
            launch = launch_json_to_model(launch_data[0])
            return create_launch_view(request, launch)
        else:
            raise Http404


def create_launch_view(request, launch):
    youtube_urls = []
    vids = launch.vid_urls.all()
    for url in vids:
        if 'youtube' in url.vid_url:
            youtube_urls.append(url.vid_url)
    return render(request, 'web/launch_page.html', {'launch': launch, 'youtube_urls': youtube_urls})


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


def launches_redirect(request,):
    return redirect('launches')