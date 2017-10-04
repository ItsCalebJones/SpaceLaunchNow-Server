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

from api import views as api_views
from bot import views as bot_views
from landing import views as landing_views
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import url, include
from rest_framework import routers


class Router(routers.DefaultRouter):
    """
    My API documentation
    """

v1_router = Router()
v1_router.register(r'launchers', api_views.LauncherViewSet)
v1_router.register(r'launcher_details', api_views.LauncherDetailViewSet)
v1_router.register(r'orbiters', api_views.OrbiterViewSet)
v1_router.register(r'launches', bot_views.LaunchViewSet)
v1_router.register(r'notifications', bot_views.NotificationViewSet)
v1_router.register(r'records', bot_views.DailyDigestRecordViewSet)


urlpatterns = [
    url(r'^v1/', include(v1_router.urls, namespace='v1')),
    url(r'^v2/', include(v1_router.urls, namespace='v2')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^docs/', include('rest_framework_docs.urls')),
    url(r'^$', landing_views.index, name='index'),
    # url(r'^launch/(?P<pk>\d+)/$', landing_views.index, name='launch_detail'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
