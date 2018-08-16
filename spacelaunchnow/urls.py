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
from django.views.generic import TemplateView

import web
from api.v310.router import api_urlpatterns as api_v310
from api.v300.router import api_urlpatterns as api_v300
from api.v200.router import api_urlpatterns as api_v2
from api.v1.router import api_urlpatterns as api_v1
from web import views as landing_views

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^v1/', include(api_v1, namespace='v1')),
    url(r'^2.0.0/', include(api_v2, namespace='v200')),
    url(r'^3.0.0/', include(api_v300, namespace='v300')),
    url(r'^3.1.0/', include(api_v310, namespace='v310')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^docs/', include('rest_framework_docs.urls')),
    url(r'^$', landing_views.index, name='index'),
    url(r'^next/', landing_views.next_launch, name='next'),
    url(r'^launch/(?P<id>\d+)/$', landing_views.launch_by_id, name='launch_by_id'),
    url(r'^launch/(?P<slug>[-\w]+)/$', landing_views.launch_by_slug, name='launch_by_slug'),
    url(r'^launch/$', landing_views.launches, name='launches'),
    url(r'^news/', include('zinnia.urls')),
    url(r'^comments/', include('django_comments.urls')),
    url(r'^app/privacy', TemplateView.as_view(template_name='web/app/privacy.html'), name='privacy'),
    url(r'^app/tos', TemplateView.as_view(template_name='web/app/tos.html'), name='tos'),
    url(r'^site/privacy', TemplateView.as_view(template_name='web/site/privacy.html'), name='privacy'),
    url(r'^site/tos', TemplateView.as_view(template_name='web/site/tos.html'), name='tos'),
    # Changing Password
    url('^', include('django.contrib.auth.urls')),
]

handler404 = web.views.handler404
handler500 = web.views.handler500
admin.site.site_header = "Space Launch Now"
admin.site.site_title = "Administration"
