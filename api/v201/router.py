from ..utils.base_router import Router
from . import views


router = Router()
router.register(r'orbiters', views.OrbiterViewSet)
router.register(r'agencies', views.AgencyViewSet)
router.register(r'launchers', views.LaunchersViewSet)
router.register(r'events', views.EventViewSet)

api_urlpatterns = router.urls
