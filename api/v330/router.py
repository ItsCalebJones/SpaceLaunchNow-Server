from ..utils.base_router import Router
from . import views


router = Router()
router.register(r'agencies', views.AgencyViewSet, base_name='agency')
router.register(r'astronaut', views.AstronautViewSet, base_name='astronauts')
router.register(r'config/launcher', views.LauncherConfigViewSet)
router.register(r'config/spacecraft', views.SpacecraftConfigViewSet)
router.register(r'events', views.EventViewSet)
router.register(r'expedition', views.ExpeditionViewSet, base_name='expedition')
router.register(r'launch/previous', views.PreviousLaunchViewSet, base_name='launch/previous')
router.register(r'launch/upcoming', views.UpcomingLaunchViewSet,  base_name='launch/upcoming')
router.register(r'launch', views.LaunchViewSet, base_name='launch')
router.register(r'launcher', views.LauncherViewSet, base_name='launcher')
router.register(r'news', views.EntryViewSet)
router.register(r'spacestations', views.SpaceStationViewSet, base_name='spacestation')
router.register(r'spacecraft', views.SpacecraftViewSet, base_name='spacecraft')
router.register(r'spacecraftflight', views.SpaceflightFlightViewSet, base_name='spacecraftflight')

api_urlpatterns = router.urls
