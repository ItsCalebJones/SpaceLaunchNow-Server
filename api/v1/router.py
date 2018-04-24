from ..utils.base_router import Router
from . import views


router = Router()
router.register(r'orbiters', views.OrbiterViewSet)
router.register(r'agency', views.AgencyViewSet)
router.register(r'launcher_details', views.LauncherDetailViewSet)

api_urlpatterns = router.urls
