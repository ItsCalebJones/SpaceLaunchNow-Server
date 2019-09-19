from datetime import datetime

import pytz
from django.contrib.sitemaps import Sitemap
from .models import Launch, Events, Astronaut, Launcher, SpaceStation


class UpcomingLaunchSitemap(Sitemap):

    def items(self):
        return Launch.objects.all().filter(net__gte=datetime.now())

    def lastmod(self, obj):
        return obj.last_updated

    def location(self, obj):
        return "/launch/" + obj.slug

    def priority(self, obj):
        current_time = datetime.now(tz=pytz.utc)
        launch_time = obj.net
        diff = int((launch_time - current_time).total_seconds())

        if diff > 0:
            if diff < 86400:
                return 1.0
            if diff < 604800:
                return 0.8
            if diff < 2.628e+6:
                return 0.6
            else:
                return 0.5
        else:
            return 0.5

    def changefreq(self, obj):
        current_time = datetime.now(tz=pytz.utc)
        launch_time = obj.net
        diff = int((launch_time - current_time).total_seconds())

        if diff > 0:
            if diff < 86400:
                return "hourly"
            if diff < 604800:
                return "daily"
            if diff < 2.628e+6:
                return "weekly"
            else:
                return "monthly"
        else:
            return "monthly"


class PreviousLaunchSitemap(Sitemap):

    def items(self):
        return Launch.objects.all().filter(net__lte=datetime.now())

    def lastmod(self, obj):
        return obj.last_updated

    def location(self, obj):
        return "/launch/" + obj.slug

    def priority(self, obj):
        current_time = datetime.now(tz=pytz.utc)
        launch_time = obj.net
        diff = abs(int((launch_time - current_time).total_seconds()))

        if diff > 0:
            if diff < 86400:
                return 1.0
            if diff < 604800:
                return 0.8
            if diff < 2.628e+6:
                return 0.6
            else:
                return 0.5
        else:
            return 0.5

    def changefreq(self, obj):
        current_time = datetime.now(tz=pytz.utc)
        launch_time = obj.net
        diff = abs(int((launch_time - current_time).total_seconds()))

        if diff > 0:
            if diff < 86400:
                return "hourly"
            if diff < 604800:
                return "daily"
            if diff < 2.628e+6:
                return "weekly"
            else:
                return "monthly"
        else:
            return "monthly"


class EventSitemap(Sitemap):
    changefreq = "weekly"

    def items(self):
        return Events.objects.all()

    def lastmod(self, obj):
        return obj.last_update

    def location(self, obj):
        return "/event/" + obj.slug

    def priority(self, obj):
        if obj.date is not None:
            current_time = datetime.now(tz=pytz.utc)
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
        return Astronaut.objects.all()

    def lastmod(self, obj):
        return datetime.now()

    def location(self, obj):
        return "/astronaut/" + obj.slug

    def priority(self, obj):
        return 0.5


class AstronautSitemap(Sitemap):
    changefreq = "weekly"

    def items(self):
        return Astronaut.objects.all()

    def lastmod(self, obj):
        return datetime.now()

    def location(self, obj):
        return "/astronaut/" + obj.slug

    def priority(self, obj):
        return 0.5


class BoosterSitemap(Sitemap):
    changefreq = "weekly"

    def items(self):
        return Launcher.objects.all()

    def lastmod(self, obj):
        return datetime.now()

    def location(self, obj):
        return "/vehicle/launcher/%s" % obj.id

    def priority(self, obj):
        return 0.5


class SpacestationSitemap(Sitemap):
    changefreq = "weekly"

    def items(self):
        return SpaceStation.objects.all()

    def lastmod(self, obj):
        return datetime.now()

    def location(self, obj):
        return "/vehicle/spacestation/%s" % obj.id

    def priority(self, obj):
        return 0.5