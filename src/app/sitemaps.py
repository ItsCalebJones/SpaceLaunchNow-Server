from api.models import Astronaut, Events, Launch, Launcher, SpaceStation
from django.contrib.sitemaps import Sitemap
from django.utils import timezone


class UpcomingLaunchSitemap(Sitemap):
    def items(self):
        return Launch.objects.all().filter(net__gte=timezone.now()).order_by("net")

    def lastmod(self, obj):
        return obj.last_updated

    def location(self, obj):
        return "/launch/" + obj.slug

    def priority(self, obj):
        current_time = timezone.now()
        launch_time = obj.net
        diff = int((launch_time - current_time).total_seconds())

        if diff > 0:
            if diff < 86400:
                return 1.0
            if diff < 604800:
                return 0.8
            if diff < 2.628e6:
                return 0.6
            else:
                return 0.5
        else:
            return 0.5

    def changefreq(self, obj):
        current_time = timezone.now()
        launch_time = obj.net
        diff = int((launch_time - current_time).total_seconds())

        if diff > 0:
            if diff < 86400:
                return "hourly"
            if diff < 604800:
                return "daily"
            if diff < 2.628e6:
                return "weekly"
            else:
                return "monthly"
        else:
            return "monthly"


class PreviousLaunchSitemap(Sitemap):
    def items(self):
        return Launch.objects.all().filter(net__lte=timezone.now()).order_by("-net")

    def lastmod(self, obj):
        return obj.last_updated

    def location(self, obj):
        return "/launch/" + obj.slug

    def priority(self, obj):
        current_time = timezone.now()
        launch_time = obj.net
        diff = abs(int((launch_time - current_time).total_seconds()))

        if diff > 0:
            if diff < 86400:
                return 1.0
            if diff < 604800:
                return 0.8
            if diff < 2.628e6:
                return 0.6
            else:
                return 0.5
        else:
            return 0.5

    def changefreq(self, obj):
        current_time = timezone.now()
        launch_time = obj.net
        diff = abs(int((launch_time - current_time).total_seconds()))

        if diff > 0:
            if diff < 86400:
                return "hourly"
            if diff < 604800:
                return "daily"
            if diff < 2.628e6:
                return "weekly"
            else:
                return "monthly"
        else:
            return "monthly"


class EventSitemap(Sitemap):
    changefreq = "weekly"

    def items(self):
        return Events.objects.all().order_by("date")

    def lastmod(self, obj):
        return obj.last_updated

    def location(self, obj):
        return "/event/" + obj.slug

    def priority(self, obj):
        if obj.date is not None:
            current_time = timezone.now()
            event_time = obj.date
            diff = int((event_time - current_time).total_seconds())

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
        return 0.5


class AstronautSitemap(Sitemap):
    changefreq = "weekly"

    def items(self):
        return Astronaut.objects.all().order_by("date_of_birth")

    def lastmod(self, obj):
        return timezone.now()

    def location(self, obj):
        return "/astronaut/" + obj.slug

    def priority(self, obj):
        return 0.5


class BoosterSitemap(Sitemap):
    changefreq = "weekly"

    def items(self):
        return Launcher.objects.all().order_by("id")

    def lastmod(self, obj):
        return timezone.now()

    def location(self, obj):
        return f"/vehicle/launcher/{obj.id}"

    def priority(self, obj):
        return 0.5


class SpacestationSitemap(Sitemap):
    changefreq = "weekly"

    def items(self):
        return SpaceStation.objects.all().order_by("id")

    def lastmod(self, obj):
        return timezone.now()

    def location(self, obj):
        return f"/vehicle/spacestation/{obj.id}"

    def priority(self, obj):
        return 0.5
