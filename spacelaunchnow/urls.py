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
from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView

import web

from api.sitemaps import (
    UpcomingLaunchSitemap,
    EventSitemap,
    PreviousLaunchSitemap,
    AstronautSitemap,
    BoosterSitemap,
    SpacestationSitemap
)

from api.endpoints.sln.v300.router import api_urlpatterns as api_v300
from api.endpoints.sln.v310.router import api_urlpatterns as api_v310
from api.endpoints.sln.v320.router import api_urlpatterns as api_v320
from api.endpoints.sln.v330.router import api_urlpatterns as api_v330
from api.endpoints.sln.v340.router import api_urlpatterns as api_v340
from api.endpoints.sln.v350.router import api_urlpatterns as api_v350
from api.endpoints.library.v200.router import api_urlpatterns as api_vll2

from spacelaunchnow import settings
from web import views as landing_views
from app.views import staff_view, translator_view, about_view
from web.sitemaps import StaticViewSitemap
from web.views import LauncherConfigListView, LaunchFeed, EventFeed, LaunchListView

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

sitemaps = {
    'static': StaticViewSitemap,
    'upcoming': UpcomingLaunchSitemap,
    'previous': PreviousLaunchSitemap,
    'events': EventSitemap,
    'astronauts': AstronautSitemap,
    'boosters': BoosterSitemap,
    'spacestations': SpacestationSitemap,

}
default_settings = [
    url(r'^robots\.txt', include('robots.urls')),
    url(r'^sitemap\.xml/$', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
]
api_settings = []
web_settings = []
admin_settings = []
debug_settings = []


def get_v350():
    v350_api = [
        url(r'^api/3.5.0/', include(api_v350, namespace='v350')),
    ]
    v350_api_schema_view = get_schema_view(
        openapi.Info(
            title="Space launch Now",
            default_version='v3.5.0',
            description="The Space Launch Now API is a up-to-date database of Spaceflight events.",
            terms_of_service="https://spacelaunchnow.me/site/tos",
            contact=openapi.Contact(email="support@spacelaunchnow.me"),
            license=openapi.License(name="Apache License 2.0"),
        ),
        patterns=v350_api,
        public=True, permission_classes=(permissions.AllowAny,),
    )

    v350_api_docs = [
        url(r'^api/3.5.0/swagger(?P<format>\.json|\.yaml)$', v350_api_schema_view.without_ui(cache_timeout=0),
            name='schema-json'),
        url(r'^api/3.5.0/swagger$', v350_api_schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
        url(r'^api/3.5.0/redoc/$', v350_api_schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    ]
    return v350_api + v350_api_docs


if settings.IS_API:
    api_settings = [

        url(r'^3.0.0/', include(api_v300, namespace='v300')),
        url(r'^3.1.0/', include(api_v310, namespace='v310')),
        url(r'^3.2.0/', include(api_v320, namespace='v320')),
        url(r'^api/3.3.0/', include(api_v330, namespace='v330')),
        url(r'^api/3.4.0/', include(api_v340, namespace='v340')),
        url(r'^api/ll/2.0.0/', include(api_vll2, namespace='ll2')),
        url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    ]
    api_settings = api_settings + get_v350()

if settings.IS_WEBSERVER:
    web_settings = [
        url(r'^\.well-known/assetlinks\.json', landing_views.asset_file),
        url(r'^ads\.txt', include('ads_txt.urls')),
        url(r'^next/', landing_views.next_launch, name='next'),
        url(r'^launch/$', LaunchListView.as_view()),
        url(r'^launch/upcoming/$', landing_views.launches, name='launches'),
        url(r'^launch/previous/$', landing_views.previous, name='previous'),

        url(r'^launch/upcoming/spacex$', landing_views.launches_spacex, name='launches_spacex'),
        url(r'^launch/upcoming/florida$', landing_views.launches_florida, name='launches_florida'),
        url(r'^launch/upcoming/vandenberg$', landing_views.launches_vandenberg, name='launches_vandenberg'),
        url(r'^spacex/$', landing_views.launches_spacex, name='direct_launches_spacex'),
        url(r'^florida/$', landing_views.launches_florida, name='direct_launches_florida'),


        url(r'^launch/(?P<id>\d+)/$', landing_views.launch_by_id, name='launch_by_id'),
        url(r'^launch/(?P<slug>[-\w]+)/$', landing_views.launch_by_slug, name='launch_by_slug'),
        url(r'^starship/$', landing_views.starship_page, name='starship_page'),
        url(r'^event/$', landing_views.events_list, name='events_list'),
        url(r'^event/(?P<id>\d+)/$', landing_views.event_by_id, name='event_by_id'),
        url(r'^event/(?P<slug>[-\w]+)/$', landing_views.event_by_slug, name='event_by_slug'),
        url(r'^vehicle/$', landing_views.vehicle_root, name='vehicle_root'),
        url(r'^vehicle/launcher$', landing_views.booster_reuse, name='booster_reuse'),
        url(r'^vehicle/launcher/(?P<id>\d+)/$', landing_views.booster_reuse_id, name='booster_reuse_id'),
        url(r'^vehicle/launcher/search/?$', landing_views.booster_reuse_search, name='booster_reuse_search'),
        url(r'^vehicle/launch_vehicle$', LauncherConfigListView.as_view()),
        url(r'^vehicle/launch_vehicle/(\d+)/', landing_views.launch_vehicle_id, name='launch_vehicle_id'),
        url(r'^vehicle/spacestation$', landing_views.spacestation_list, name='spacestation_list'),
        url(r'^vehicle/spacestation/(?P<id>\d+)/$', landing_views.spacestation_by_id, name='spacestation_by_id'),
        url(r'^vehicle/spacecraft$', landing_views.spacecraft_list, name='spacecraft_list'),
        url(r'^vehicle/spacecraft/(?P<id>\d+)/$', landing_views.spacecraft_by_id, name='spacecraft_by_id'),
        url(r'^astronaut/$', landing_views.astronaut_list, name='astronauts'),
        url(r'^astronaut/search/?$', landing_views.astronaut_search, name='astronaut_search'),
        url(r'^astronaut/(?P<id>\d+)/$', landing_views.astronaut, name='astronaut_by_id'),
        url(r'^astronaut/(?P<slug>[-\w]+)/$', landing_views.astronaut_by_slug, name='astronaut_by_slug'),
        url(r'^about/$', about_view, name='staff'),
        url(r'^about/staff/$', staff_view, name='staff'),
        url(r'^about/translators/$', translator_view, name='translators'),
        url(r'^app/privacy', TemplateView.as_view(template_name='web/app/privacy.html'), name='privacy'),
        url(r'^app/tos', TemplateView.as_view(template_name='web/app/tos.html'), name='tos'),
        url(r'^site/privacy', TemplateView.as_view(template_name='web/site/privacy.html'), name='privacy'),
        url(r'^site/tos', TemplateView.as_view(template_name='web/site/tos.html'), name='tos'),
        url(r'^ajax/astronaut/$', landing_views.astronaut_search_ajax, name='ajax-astronaut'),
        url(r'^app$', landing_views.app, name='app'),
        url(r'^$', landing_views.index, name='index'),
        url(r'^launches/latest/feed.ics$', LaunchFeed()),
        url(r'^events/latest/feed.ics$', EventFeed()),
        url(r'^tz_detect/', include('tz_detect.urls')),
    ]

if settings.IS_ADMIN:
    admin_settings = [
        url(r'^jet/', include('jet.urls', 'jet')),  # Django JET URLS
        url(r'^jet/dashboard/', include('jet.dashboard.urls', 'jet-dashboard')),  # Django JET dashboard URLS
        url(r'^admin/', include(admin.site.urls)),
        url('^', include('django.contrib.auth.urls')),
        url(r'^signup/$', landing_views.signup, name='signup'),
    ]

if settings.DEBUG:
    import debug_toolbar

    debug_settings = [
        url(r'^__debug__/', include(debug_toolbar.urls)),

        # For django versions before 2.0:
        # url(r'^__debug__/', include(debug_toolbar.urls)),

    ]

urlpatterns = default_settings + api_settings + web_settings + admin_settings + debug_settings


handler404 = web.views.handler404
handler500 = web.views.handler500
admin.site.site_header = "Space Launch Now"
admin.site.site_title = "Administration"
