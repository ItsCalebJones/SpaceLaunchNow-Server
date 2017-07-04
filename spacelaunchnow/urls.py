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
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import url, include
from rest_framework import routers


class Router(routers.DefaultRouter):
    """
    My API documentation
    """

router = Router()
router.register(r'launchers', api_views.LauncherViewSet)
router.register(r'launcher_details', api_views.LauncherDetailViewSet)
router.register(r'orbiters', api_views.OrbiterViewSet)
router.register(r'launches', bot_views.LaunchViewSet)
router.register(r'notifications', bot_views.NotificationViewSet)
router.register(r'records', bot_views.DailyDigestRecordViewSet)


urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^docs/', include('rest_framework_docs.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
