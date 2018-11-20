from datetime import datetime

import pytz
from django.contrib.sitemaps import Sitemap
from .models import Launch


class LaunchSitemap(Sitemap):
    changefreq = "daily"

    def items(self):
        return Launch.objects.all()

    def lastmod(self, obj):
        return obj.last_updated

    def location(self, obj):
        return "/launch/" + obj.slug

    def priority(self, obj):
        current_time = datetime.now(tz=pytz.utc)
        launch_time = obj.net
        diff = int((launch_time - current_time).total_seconds())

        if diff < 0:
            if diff > -86400:
                return 1.0
            if diff > -604800:
                return 0.8
            else:
                return 0.3
        elif diff > 0:
            if diff < 86400:
                return 1.0
            if diff < 604800:
                return 0.8
            else:
                return 0.5
        else:
            return 0.5
