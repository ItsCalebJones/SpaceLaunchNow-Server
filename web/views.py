# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
from datetime import datetime
import datetime as dt

from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import render, redirect
from django import forms

# Create your views here.
from api.models import Agency, Launch, Astronaut


def get_youtube_url(launch):
    for url in launch.vid_urls.all():
        if 'youtube' in url.vid_url:
            return url.vid_url


def index(request):
    in_flight_launch = Launch.objects.filter(status__id=6).order_by('-net').first()
    if in_flight_launch:
        return render(request, 'web/index.html', {'launch': in_flight_launch,
                                                  'youtube_url': get_youtube_url(in_flight_launch)})

    recently_launched = Launch.objects.filter(net__gte=datetime.utcnow() - dt.timedelta(hours=2),
                                              net__lte=datetime.utcnow()).order_by('-net').first()
    if recently_launched:
        return render(request, 'web/index.html', {'launch': recently_launched,
                                                  'youtube_url': get_youtube_url(recently_launched)})
    else:
        _next_launch = Launch.objects.filter(net__gte=datetime.utcnow()).order_by('net').first()
        return render(request, 'web/index.html', {'launch': _next_launch,
                                                  'youtube_url': get_youtube_url(_next_launch)})


# Create your views here.
def next_launch(request):
    in_flight_launch = Launch.objects.filter(status__id=6).order_by('-net').first()
    if in_flight_launch:
        return redirect('launch_by_slug', slug=in_flight_launch.slug)
    recently_launched = Launch.objects.filter(net__gte=datetime.utcnow() - dt.timedelta(hours=6),
                                              net__lte=datetime.utcnow()).order_by('-net').first()
    if recently_launched:
        return redirect('launch_by_slug', slug=recently_launched.slug)
    else:
        _next_launch = Launch.objects.filter(net__gte=datetime.utcnow()).order_by('net').first()
        return redirect('launch_by_slug', slug=_next_launch.slug)


# Create your views here.
def launch_by_slug(request, slug):
    try:
        return create_launch_view(request, Launch.objects.get(slug=slug))
    except ObjectDoesNotExist:
        raise Http404


# Create your views here.
def launch_by_id(request, id):
    try:
        return redirect('launch_by_slug', slug=Launch.objects.get(launch_library_id=id).slug)
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
    }[launch.status.id]


def create_launch_view(request, launch):
    youtube_urls = []
    vids = launch.vid_urls.all()
    status = get_launch_status(launch)
    agency = launch.rocket.configuration.launch_agency
    launches_good = Launch.objects.filter(rocket__configuration__launch_agency=agency, status=3)
    launches_bad = Launch.objects.filter(Q(rocket__configuration__launch_agency=agency) & Q(Q(status=4) | Q(status=7)))
    launches_pending = Launch.objects.filter(
        Q(rocket__configuration__launch_agency=agency) & Q(Q(status=1) | Q(status=2) | Q(status=5)))
    launches = {'good': launches_good, 'bad': launches_bad, 'pending': launches_pending}
    for url in vids:
        if 'youtube' in url.vid_url:
            youtube_urls.append(url.vid_url)
    previous_launches = Launch.objects.filter(net__lte=datetime.utcnow()).order_by('-net')[:10]
    return render(request, 'web/launch_page.html', {'launch': launch, 'youtube_urls': youtube_urls, 'status': status,
                                                    'agency': agency, 'launches': launches,
                                                    'previous_launches': previous_launches})


# Create your views here.
def launches(request, ):
    query = request.GET.get('q')

    if query is not None:
        _launches = Launch.objects.filter(net__gte=datetime.utcnow()).order_by('net')
        _launches = _launches.filter(Q(rocket__configuration__launch_agency__abbrev__contains=query) |
                                     Q(pad__location__name__contains=query) |
                                     Q(rocket__configuration__name__contains=query))[:15]
    else:
        _launches = Launch.objects.filter(net__gte=datetime.utcnow()).order_by('net')[:15]

    previous_launches = Launch.objects.filter(net__lte=datetime.utcnow()).order_by('-net')[:10]

    return render(request, 'web/launches.html', {'launches': _launches,
                                                 'query': query,
                                                 'previous_launches': previous_launches})


def astronaut(request, id):
    try:
        return redirect('astronaut_by_slug', slug=Astronaut.objects.get(pk=id).slug)
    except ObjectDoesNotExist:
        raise Http404


def vehicle_root(request):
    previous_launches = Launch.objects.filter(net__lte=datetime.utcnow()).order_by('-net')[:10]
    return render(request, 'web/vehicles/index.html', {'previous_launches': previous_launches})


def astronaut_by_slug(request, slug):
    try:
        _astronaut = Astronaut.objects.get(slug=slug)
        previous_list = list(
            (Launch.objects.filter(Q(rocket__spacecraftflight__launch_crew__astronaut__id=_astronaut.pk) |
                                   Q(rocket__spacecraftflight__onboard_crew__astronaut__id=_astronaut.pk) |
                                   Q(rocket__spacecraftflight__landing_crew__astronaut__id=_astronaut.pk))
             .filter(net__lte=datetime.utcnow())
             .values_list('pk', flat=True)
             .distinct()))
        upcoming_list = list(
            (Launch.objects.filter(Q(rocket__spacecraftflight__launch_crew__astronaut__id=_astronaut.pk) |
                                   Q(rocket__spacecraftflight__onboard_crew__astronaut__id=_astronaut.pk) |
                                   Q(rocket__spacecraftflight__landing_crew__astronaut__id=_astronaut.pk))
             .filter(net__gte=datetime.utcnow())
             .values_list('pk', flat=True)
             .distinct()))
        _launches = Launch.objects.filter(pk__in=previous_list).order_by('net')
        _upcoming_launches = Launch.objects.filter(pk__in=upcoming_list).order_by('net')
        previous_launches = Launch.objects.filter(net__lte=datetime.utcnow()).order_by('-net')[:5]
        return render(request, 'web/astronaut/astronaut_detail.html', {'astronaut': _astronaut,
                                                                       'previous_astronaut_launches': _launches,
                                                                       'upcoming_launches': _upcoming_launches,
                                                                       'previous_launches': previous_launches})
    except ObjectDoesNotExist:
        raise Http404


def astronaut_list(request, ):
    query = request.GET.get('status')
    if query is None:
        query = 1
    else:
        query = int(query)

    nationality = request.GET.get('nationality')

    if nationality == "American":
        astronaut_list = Astronaut.objects.only("name", "nationality", "twitter", "instagram", "wiki", "bio",
                                                "profile_image", "slug").filter(nationality="American").filter(
            status=query).order_by('name')
    elif nationality == "Russian":
        astronaut_list = Astronaut.objects.only("name", "nationality", "twitter", "instagram", "wiki", "bio",
                                                "profile_image", "slug").filter(
            Q(nationality="Russian") | Q(nationality="Soviet")).filter(status=query).order_by('name')
    elif nationality == "European":
        astronaut_list = Astronaut.objects.only("name", "nationality", "twitter", "instagram", "wiki", "bio",
                                                "profile_image", "slug").filter(
            Q(nationality="Austrain") | Q(nationality="Belarusian") | Q(nationality="Belgian")
            | Q(nationality="British") | Q(nationality="Danish") | Q(nationality="Dutch")
            | Q(nationality="French") | Q(nationality="German") | Q(nationality="Italian")
            | Q(nationality="Polish") | Q(nationality="Spanish") | Q(nationality="Swedish")
            | Q(nationality="Swiss")).filter(status=query).order_by('name')
    elif nationality == "Other":
        astronaut_list = Astronaut.objects.only("name", "nationality", "twitter", "instagram", "wiki", "bio",
                                                "profile_image", "slug").exclude(nationality="Austrain").exclude(
            nationality="Belarusian").exclude(nationality="Belgian").exclude(nationality="British").exclude(
            nationality="Danish").exclude(nationality="Dutch") \
            .exclude(nationality="French").exclude(nationality="German") \
            .exclude(nationality="Italian").exclude(nationality="Polish") \
            .exclude(nationality="Spanish").exclude(nationality="Swedish") \
            .exclude(nationality="Swiss").exclude(nationality="American").exclude(nationality="Russian").exclude(
            nationality="Soviet").filter(status=query).order_by('name')
    else:
        astronaut_list = Astronaut.objects.only("name", "nationality", "twitter", "instagram", "wiki", "bio",
                                                "profile_image", "slug").filter(status=query).order_by('name')

    previous_launches = Launch.objects.only("slug", "net", "name", "status__name", "mission__name",
                                            "mission__description", "rocket__configuration__name").prefetch_related(
        'info_urls').prefetch_related('vid_urls').select_related('rocket').prefetch_related('mission').prefetch_related(
        'rocket__configuration').prefetch_related('rocket__configuration__launch_agency').prefetch_related(
        'mission__mission_type').prefetch_related('status').filter(net__lte=datetime.utcnow()).order_by('-net')[:10]

    page = request.GET.get('page', 1)

    paginator = Paginator(astronaut_list, 9)

    try:
        astronauts = paginator.page(page)
    except PageNotAnInteger:
        astronauts = paginator.page(1)
    except EmptyPage:
        astronauts = paginator.page(paginator.num_pages)

    return render(request, 'web/astronaut/astronaut_list.html', {'astronauts': astronauts,
                                                                 'previous_launches': previous_launches,
                                                                 'status': query,
                                                                 'nationality': nationality})


def handler404(request):
    return render(request, 'web/404.html', status=404)


def handler500(request):
    return render(request, 'web/500.html', status=500)


def launches_redirect(request, ):
    return redirect('launches')


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    last_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.')

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)

        for fieldname in ['password1']:
            self.fields[fieldname].help_text = None

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2',)
        help_texts = {
            'password1': None,
        }


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('/admin/')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})


def astronaut_search(request):
    query = request.GET.get('q')

    if query is not None:
        _astronauts = Astronaut.objects.filter(name__icontains=query).order_by('name')
        previous_launches = Launch.objects.filter(net__lte=datetime.utcnow()).order_by('-net')[:5]
        return render(request, 'web/astronaut/astronaut_search.html', {'astronauts': _astronauts,
                                                                       'query': query,
                                                                       'previous_launches': previous_launches})
    else:
        return redirect('astronauts')


def astronaut_search_ajax(request):
    query = request.GET.get('q')

    if not query:
        return HttpResponse(json.dumps([{}]), content_type='application/json')
    majors = Astronaut.objects.filter(name__icontains=query)
    return HttpResponse(
        json.dumps(majors),
        content_type='application/json',
    )
