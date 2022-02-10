# website/context_processors.py
from django.conf import settings


def ga_tracking_id(request):
    return {"ga_tracking_id": settings.GA_TRACKING_ID}


def use_google_analytics(request):
    return {"use_google_analytics": settings.USE_GA}
