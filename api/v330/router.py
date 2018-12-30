from ..utils.base_router import Router
from . import views


router = Router()
router.register(r'agencies', views.AgencyViewSet, base_name='agency')
router.register(r'astronauts', views.AstronautViewSet, base_name='astronauts')
router.register(r'events', views.EventViewSet)
router.register(r'launch/previous', views.PreviousLaunchViewSet, base_name='launch/previous')
router.register(r'launch/upcoming', views.UpcomingLaunchViewSet,  base_name='launch/upcoming')
router.register(r'launch', views.LaunchViewSet, base_name='launch')
router.register(r'launcher', views.LauncherViewSet, base_name='launcher')
router.register(r'launcher_config', views.LauncherConfigViewSet)
router.register(r'news', views.EntryViewSet)
router.register(r'spacecraft_config', views.SpacecraftConfigViewSet)
router.register(r'spacestations', views.SpaceStationViewSet, base_name='spacestation')
router.register(r'spacecraftflights', views.SpaceflightFlightViewSet, base_name='spacecraftflights')

api_urlpatterns = router.urls
