from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    priority = 1
    changefreq = "daily"

    def items(self):
        return ["launches_spacex", "launches_florida", "launches_vandenberg"]

    def location(self, item):
        return reverse(item)
