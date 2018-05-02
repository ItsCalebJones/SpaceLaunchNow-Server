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

from api.v200.router import api_urlpatterns as api_v2
from api.v1.router import api_urlpatterns as api_v1
from web import views as landing_views


urlpatterns = [
    url(r'^jet/', include('jet.urls', 'jet')),  # Django JET URLS
    url(r'^admin/', include(admin.site.urls)),
    url(r'^v1/', include(api_v1, namespace='v1')),
    url(r'^2.0.0/', include(api_v2, namespace='v200')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^docs/', include('rest_framework_docs.urls')),
    url(r'^$', landing_views.index, name='index'),
    url(r'^next/', landing_views.next_launch, name='next'),
    url(r'^launch/(?P<pk>\d+)/$', landing_views.launch_by_id, name='launch_by_id'),
    url(r'^launch/$', landing_views.launches, name='launches'),
    url(r'^privacy', TemplateView.as_view(template_name='web/privacy.html'), name='privacy'),
    url(r'^tos', TemplateView.as_view(template_name='web/tos.html'), name='tos'),
    # Changing Password
    url('^', include('django.contrib.auth.urls')),
]

admin.site.site_header = "Space Launch Now"
admin.site.site_title = "Administration"
