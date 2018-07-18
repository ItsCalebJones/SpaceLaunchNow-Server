# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import ObjectDoesNotExist
from django.template.defaultfilters import slugify
from datetime import datetime
from django.db.models import Q
from django.http import Http404, HttpResponseNotFound
from django.shortcuts import render, redirect

# Create your views here.
from api.models import Agency, Launch


def index(request):
    return render(request, 'web/index.html',)


# Create your views here.
def next_launch(request):
    launch = Launch.objects.filter(net__gt=datetime.now()).order_by('net').first()
    if launch:
        return redirect('launch_by_slug', slug=launch.slug)
    else:
        return redirect('launches')


# Create your views here.
def launch_by_slug(request, slug):
    try:
        return create_launch_view(request, Launch.objects.get(slug=slug))
    except ObjectDoesNotExist:
        raise Http404


# Create your views here.
def launch_by_id(request, id):
    try:
        return redirect('launch_by_slug', slug=Launch.objects.get(pk=id).slug)
    except ObjectDoesNotExist:
        raise Http404


def get_launch_status(launch):
    return {
        1: 'Go for Launch',
        2: 'Launch is NO-GO',
        3: 'Successful Launch',
        4: 'Launch Failed',
        5: 'Unplanned Hold',
        6: 'In Flight',
        7: 'Partial Failure',
    }[launch.status]


def create_launch_view(request, launch):
    youtube_urls = []
    vids = launch.vid_urls.all()
    status = launch.status_name
    agency = launch.lsp
    launches_good = Launch.objects.filter(lsp=launch.lsp, status=3)
    launches_bad = Launch.objects.filter(lsp=launch.lsp, status=4)
    launches_pending = Launch.objects.filter(Q(lsp=launch.lsp) & Q(Q(status=1) | Q(status=2)))
    launches = {'good': launches_good, 'bad': launches_bad, 'pending': launches_pending}
    for url in vids:
        if 'youtube' in url.vid_url:
            youtube_urls.append(url.vid_url)
    return render(request, 'web/launch_page.html', {'launch': launch, 'youtube_urls': youtube_urls, 'status': status,
                                                    'agency': agency, 'launches': launches})


# Create your views here.
def launches(request,):
    query = request.GET.get('q')

    if query is not None:
        _launches = Launch.objects.filter(net__gt=datetime.now()).order_by('net')
        _launches = _launches.filter(lsp__abbrev__contains=query)[:5]
    else:
        _launches = Launch.objects.filter(net__gt=datetime.now()).order_by('net')[:5]

    if _launches:
        return render(request, 'web/launches.html', {'launches': _launches, 'query': query})
    else:
        raise Http404


def handler404(request):
    return render(request, 'web/404.html', status=404)


def handler500(request):
    return render(request, 'web/500.html', status=500)


def launches_redirect(request,):
    return redirect('launches')
