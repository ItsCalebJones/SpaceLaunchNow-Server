from rest_framework import routers


class SpaceLaunchNowView(routers.APIRootView):
    """
    Space Launch Now's public API - for more information join our discord!
    """
    pass


class Router(routers.DefaultRouter):
    APIRootView = SpaceLaunchNowView
