from api.v330.agencies.views import AgencyViewSet
from api.v330.astronaut.views import AstronautViewSet
from api.v330.config.launcher.views import LauncherConfigViewSet
from api.v330.config.spacecraft.views import SpacecraftConfigViewSet
from api.v330.docking_event.views import DockingEventViewSet
from api.v330.events.views import EventViewSet
from api.v330.expedition.views import ExpeditionViewSet
from api.v330.launch.views import PreviousLaunchViewSet, UpcomingLaunchViewSet, LaunchViewSet
from api.v330.launcher.views import LauncherViewSet
from api.v330.spacecraft.flight.views import SpaceflightFlightViewSet
from api.v330.spacecraft.views import SpacecraftViewSet
from api.v330.spacestation.views import SpaceStationViewSet
from ..utils.base_router import Router


router = Router()
router.register(r'agencies', AgencyViewSet, base_name='agency')
router.register(r'astronaut', AstronautViewSet, base_name='astronaut')
router.register(r'config/launcher', LauncherConfigViewSet)
router.register(r'config/spacecraft', SpacecraftConfigViewSet)
router.register(r'docking_event', DockingEventViewSet)
router.register(r'event', EventViewSet)
router.register(r'expedition', ExpeditionViewSet, base_name='expedition')
router.register(r'launch/previous', PreviousLaunchViewSet, base_name='launch/previous')
router.register(r'launch/upcoming', UpcomingLaunchViewSet,  base_name='launch/upcoming')
router.register(r'launch', LaunchViewSet, base_name='launch')
router.register(r'launcher', LauncherViewSet, base_name='launcher')
router.register(r'spacestation', SpaceStationViewSet, base_name='spacestation')
router.register(r'spacecraft/flight', SpaceflightFlightViewSet, base_name='spacecraftflight')
router.register(r'spacecraft', SpacecraftViewSet, base_name='spacecraft')

api_urlpatterns = router.urls
