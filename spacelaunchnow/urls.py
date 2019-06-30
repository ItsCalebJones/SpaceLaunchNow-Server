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
from api.v330.router import api_urlpatterns as api_v330
from api.v331.router import api_urlpatterns as api_v331
from api.sitemaps import LaunchSitemap
from api.v320.router import api_urlpatterns as api_v320
from api.v310.router import api_urlpatterns as api_v310
from api.v300.router import api_urlpatterns as api_v300
from api.v200.router import api_urlpatterns as api_v2
from api.v1.router import api_urlpatterns as api_v1
from spacelaunchnow import config
from web import views as landing_views
from app.views import staff_view, translator_view, about_view
from web.views import LauncherConfigListView

sitemaps = {
    'posts': LaunchSitemap
}
default_settings = [
    url(r'^robots\.txt', include('robots.urls')),
    url(r'^sitemap\.xml/$', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    url(r'^news/', include('zinnia.urls')),
]
api_settings = []
web_settings = []
admin_settings = []
if config.IS_API:
    api_settings = [
        url(r'^v1/', include(api_v1, namespace='v1')),
        url(r'^2.0.0/', include(api_v2, namespace='v200')),
        url(r'^3.0.0/', include(api_v300, namespace='v300')),
        url(r'^3.1.0/', include(api_v310, namespace='v310')),
        url(r'^3.2.0/', include(api_v320, namespace='v320')),
        url(r'^api/3.3.0/', include(api_v330, namespace='v330')),
        url(r'^api/3.3.1/', include(api_v331, namespace='v331')),
        url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    ]
if config.IS_WEBSERVER:
    web_settings = [
        url(r'^ads\.txt', include('ads_txt.urls')),
        url(r'^next/', landing_views.next_launch, name='next'),
        url(r'^launch/(?P<id>\d+)/$', landing_views.launch_by_id, name='launch_by_id'),
        url(r'^launch/(?P<slug>[-\w]+)/$', landing_views.launch_by_slug, name='launch_by_slug'),
        url(r'^launch/$', landing_views.launches, name='launches'),
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
        url(r'^about/staff/translators/$', translator_view, name='translators'),
        url(r'^comments/', include('django_comments.urls')),
        url(r'^app/privacy', TemplateView.as_view(template_name='web/app/privacy.html'), name='privacy'),
        url(r'^app/tos', TemplateView.as_view(template_name='web/app/tos.html'), name='tos'),
        url(r'^site/privacy', TemplateView.as_view(template_name='web/site/privacy.html'), name='privacy'),
        url(r'^site/tos', TemplateView.as_view(template_name='web/site/tos.html'), name='tos'),
        url(r'^docs/', include('rest_framework_docs.urls')),
        url(r'^ajax/astronaut/$', landing_views.astronaut_search_ajax, name='ajax-astronaut'),
        url(r'^app$', landing_views.app, name='app'),
        url(r'^$', landing_views.index, name='index'),
    ]

if config.IS_ADMIN:
    admin_settings = [
        url(r'^jet/', include('jet.urls', 'jet')),  # Django JET URLS
        url(r'^jet/dashboard/', include('jet.dashboard.urls', 'jet-dashboard')),  # Django JET dashboard URLS
        url(r'^admin/', include(admin.site.urls)),
        url('^', include('django.contrib.auth.urls')),
        url(r'^signup/$', landing_views.signup, name='signup'),
    ]


urlpatterns = default_settings + api_settings + web_settings + admin_settings

if config.DEBUG:
    import debug_toolbar

    urlpatterns = [
                      url(r'^__debug__/', include(debug_toolbar.urls)),

                      # For django versions before 2.0:
                      # url(r'^__debug__/', include(debug_toolbar.urls)),

                  ] + urlpatterns

handler404 = web.views.handler404
handler500 = web.views.handler500
admin.site.site_header = "Space Launch Now"
admin.site.site_title = "Administration"
