"""spacelaunchnow URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from api.endpoints.library.v200.router import api_urlpatterns as ll_api_v200
from api.endpoints.library.v210.router import api_urlpatterns as ll_api_v210
from api.endpoints.library.v220.router import api_urlpatterns as ll_api_v220
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponse
from django.urls import include, path, re_path
from django.views.generic import TemplateView

import web
from app.sitemaps import (
    AstronautSitemap,
    BoosterSitemap,
    EventSitemap,
    PreviousLaunchSitemap,
    SpacestationSitemap,
    UpcomingLaunchSitemap,
)
from app.views import about_view, staff_view, translator_view
from spacelaunchnow import settings
from web import views as landing_views
from web.sitemaps import StaticViewSitemap
from web.views import AdsView, EventFeed, LauncherConfigListView, LaunchFeed, LaunchListView

sitemaps = {
    "static": StaticViewSitemap,
    "upcoming": UpcomingLaunchSitemap,
    "previous": PreviousLaunchSitemap,
    "events": EventSitemap,
    "astronauts": AstronautSitemap,
    "boosters": BoosterSitemap,
    "spacestations": SpacestationSitemap,
}
default_settings = [
    re_path(r"^robots\.txt", include("robots.urls")),
    re_path(r"^sitemap\.xml/$", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("health_check/", include("health_check.urls")),
]
api_settings = []
web_settings = []
admin_settings = []
debug_settings = []


def get_v200():
    v200_api = [
        re_path(r"^api/ll/2.0.0/", include(ll_api_v200)),
    ]
    return v200_api


def get_v210():
    v210_api = [
        re_path(r"^api/ll/2.1.0/", include(ll_api_v210)),
    ]
    return v210_api


def get_v220():
    v220_api = [
        re_path(r"^api/ll/2.2.0/", include((ll_api_v220, "v2.2.0"))),
    ]
    return v220_api


if settings.IS_API:
    api_settings = [
        path("api-auth/", include("rest_framework.urls")),
    ]
    api_settings = api_settings + get_v200() + get_v210() + get_v220()

if settings.IS_WEBSERVER:

    def health(request):
        return HttpResponse("ok", content_type="text/plain")

    web_settings = [
        re_path("_health/", health),
        re_path(r"^\.well-known/assetlinks\.json", landing_views.asset_file),
        re_path(r"^app-ads\.txt", AdsView.as_view()),
        re_path(r"^ads\.txt", AdsView.as_view()),
        path("", landing_views.index, name="index"),
        re_path(r"^next/", landing_views.next_launch, name="next"),
        path("launch/", LaunchListView.as_view()),
        path("launch/upcoming/", landing_views.launches, name="launches"),
        path("launch/previous/", landing_views.previous, name="previous"),
        path("launch/upcoming/spacex", landing_views.launches_spacex, name="launches_spacex"),
        path("launch/upcoming/florida", landing_views.launches_florida, name="launches_florida"),
        path("launch/upcoming/vandenberg", landing_views.launches_vandenberg, name="launches_vandenberg"),
        path("spacex/", landing_views.launches_spacex, name="direct_launches_spacex"),
        path("florida/", landing_views.launches_florida, name="direct_launches_florida"),
        path("launch/<int:id>/", landing_views.launch_by_id, name="launch_by_id"),
        re_path(r"^launch/(?P<slug>[-\w]+)/$", landing_views.launch_by_slug, name="launch_by_slug"),
        path("starship/", landing_views.starship_page, name="starship_page"),
        path("event/", landing_views.events_list, name="events_list"),
        path("event/<int:id>/", landing_views.event_by_id, name="event_by_id"),
        re_path(r"^event/(?P<slug>[-\w]+)/$", landing_views.event_by_slug, name="event_by_slug"),
        path("vehicle/", landing_views.vehicle_root, name="vehicle_root"),
        path("vehicle/launcher", landing_views.booster_reuse, name="booster_reuse"),
        path("vehicle/launcher/<int:id>/", landing_views.booster_reuse_id, name="booster_reuse_id"),
        re_path(r"^vehicle/launcher/search/?$", landing_views.booster_reuse_search, name="booster_reuse_search"),
        path("vehicle/launch_vehicle", LauncherConfigListView.as_view()),
        re_path(r"^vehicle/launch_vehicle/(\d+)/", landing_views.launch_vehicle_id, name="launch_vehicle_id"),
        path("vehicle/spacestation", landing_views.spacestation_list, name="spacestation_list"),
        path("vehicle/spacestation/<int:id>/", landing_views.spacestation_by_id, name="spacestation_by_id"),
        path("vehicle/spacecraft", landing_views.spacecraft_list, name="spacecraft_list"),
        path("vehicle/spacecraft/<int:id>/", landing_views.spacecraft_by_id, name="spacecraft_by_id"),
        path("astronaut/", landing_views.astronaut_list, name="astronauts"),
        re_path(r"^astronaut/search/?$", landing_views.astronaut_search, name="astronaut_search"),
        path("astronaut/<int:id>/", landing_views.astronaut, name="astronaut_by_id"),
        re_path(r"^astronaut/(?P<slug>[-\w]+)/$", landing_views.astronaut_by_slug, name="astronaut_by_slug"),
        path("about/", about_view, name="staff"),
        path("about/staff/", staff_view, name="staff"),
        path("about/translators/", translator_view, name="translators"),
        re_path(r"^app/privacy", TemplateView.as_view(template_name="web/app/privacy.html"), name="privacy"),
        re_path(r"^app/tos", TemplateView.as_view(template_name="web/app/tos.html"), name="tos"),
        re_path(r"^site/privacy", TemplateView.as_view(template_name="web/site/privacy.html"), name="privacy"),
        re_path(r"^site/tos", TemplateView.as_view(template_name="web/site/tos.html"), name="tos"),
        path("ajax/astronaut/", landing_views.astronaut_search_ajax, name="ajax-astronaut"),
        path("app", landing_views.app, name="app"),
        re_path(r"^launches/latest/feed.ics$", LaunchFeed()),
        re_path(r"^events/latest/feed.ics$", EventFeed()),
        path("tz_detect/", include("tz_detect.urls")),
        re_path(r"^lazy_load_updates/(?P<id>[-\w]+)/$", landing_views.lazy_load_updates, name="lazy_load_updates"),
    ]

if settings.IS_ADMIN:
    admin_settings = [
        path("jet/", include("jet.urls", "jet")),  # Django JET URLS
        path("jet/dashboard/", include("jet.dashboard.urls", "jet-dashboard")),  # Django JET dashboard URLS
        re_path(r"^admin/", admin.site.urls),
        path("", include("django.contrib.auth.urls")),
        path("signup/", landing_views.signup, name="signup"),
    ]

if settings.DEBUG:
    import debug_toolbar

    debug_settings = [
        path("__debug__/", include(debug_toolbar.urls)),
        # For django versions before 2.0:
        # url(r'^__debug__/', include(debug_toolbar.urls)),
    ]

urlpatterns = default_settings + api_settings + web_settings + admin_settings + debug_settings


handler404 = web.views.handler404
handler500 = web.views.handler500
admin.site.site_header = "Space Launch Now"
admin.site.site_title = "Administration"
