"""Tests for RoundTimeFiltersMiddleware.

The apps send datetime range filters to the microsecond, so without rounding
every request builds unique SQL and cachalot never gets a hit. During a large
launch that sent every API call to Postgres and pinned its CPU at 100%.
"""

from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings

from spacelaunchnow.middleware import RoundTimeFiltersMiddleware


def _run(url):
    """Pass a GET request for ``url`` through the middleware; return the request the view saw."""
    seen = {}

    def view(request):
        seen["request"] = request
        return HttpResponse()

    RoundTimeFiltersMiddleware(view)(RequestFactory().get(url))
    return seen["request"]


class RoundTimeFiltersMiddlewareTests(SimpleTestCase):
    def test_lower_bound_rounds_down_to_the_minute(self):
        request = _run("/api/ll/2.4.0/launches/?net__gt=2026-10-01T14:03:15.329048Z&limit=4")
        self.assertEqual(request.GET["net__gt"], "2026-10-01T14:03:00Z")
        self.assertEqual(request.GET["limit"], "4")

    def test_upper_bound_rounds_up_to_the_minute(self):
        request = _run("/api/ll/2.4.0/launches/mini/?net__lt=2026-10-08T15:03:32.167625Z")
        self.assertEqual(request.GET["net__lt"], "2026-10-08T15:04:00Z")

    def test_gte_and_lte_follow_the_same_directions(self):
        request = _run("/api/ll/2.4.0/launches/?net__gte=2026-10-01T14:03:59Z&net__lte=2026-10-01T14:03:01Z")
        self.assertEqual(request.GET["net__gte"], "2026-10-01T14:03:00Z")
        self.assertEqual(request.GET["net__lte"], "2026-10-01T14:04:00Z")

    def test_requests_in_the_same_minute_share_one_query_string(self):
        first = _run("/api/ll/2.4.0/launches/?limit=4&net__gt=2026-10-01T14:03:05.260Z&ordering=net")
        second = _run("/api/ll/2.4.0/launches/?limit=4&net__gt=2026-10-01T14:03:51.790719Z&ordering=net")
        self.assertEqual(first.META["QUERY_STRING"], second.META["QUERY_STRING"])
        self.assertEqual(first.GET, second.GET)

    def test_query_string_matches_rounded_params(self):
        request = _run("/api/ll/2.4.0/launches/?net__gt=2026-10-01T14:03:15.329048Z")
        self.assertEqual(request.META["QUERY_STRING"], "net__gt=2026-10-01T14%3A03%3A00Z")

    def test_offset_timestamps_are_rounded_in_utc(self):
        request = _run("/api/ll/2.4.0/launches/?net__gt=2026-10-01T10:03:15-04:00")
        self.assertEqual(request.GET["net__gt"], "2026-10-01T14:03:00Z")

    def test_naive_timestamps_stay_naive(self):
        request = _run("/api/ll/2.4.0/launches/?net__gt=2026-10-01T14:03:15.5")
        self.assertEqual(request.GET["net__gt"], "2026-10-01T14:03:00")

    def test_values_already_on_a_boundary_are_untouched(self):
        url = "/api/ll/2.4.0/launches/?net__gt=2026-10-01T14:03:00.000Z"
        request = _run(url)
        self.assertEqual(request.GET["net__gt"], "2026-10-01T14:03:00.000Z")
        self.assertEqual(request.META["QUERY_STRING"], url.split("?", 1)[1])

    def test_non_datetime_range_values_are_untouched(self):
        request = _run("/api/ll/2.4.0/launches/?id__gt=5&net__gte=2026-10-01&net__lt=not-a-date")
        self.assertEqual(request.GET["id__gt"], "5")
        self.assertEqual(request.GET["net__gte"], "2026-10-01")
        self.assertEqual(request.GET["net__lt"], "not-a-date")

    def test_other_params_are_untouched(self):
        request = _run("/api/ll/2.4.0/launches/?search=2026-10-01T14:03:15Z&net__gt=2026-10-01T14:03:15Z")
        self.assertEqual(request.GET["search"], "2026-10-01T14:03:15Z")

    def test_repeated_params_are_all_rounded(self):
        request = _run("/api/ll/2.4.0/launches/?net__gt=2026-10-01T14:03:15Z&net__gt=2026-10-01T15:07:45Z")
        self.assertEqual(request.GET.getlist("net__gt"), ["2026-10-01T14:03:00Z", "2026-10-01T15:07:00Z"])

    def test_non_api_paths_are_untouched(self):
        request = _run("/launch/?net__gt=2026-10-01T14:03:15.329048Z")
        self.assertEqual(request.GET["net__gt"], "2026-10-01T14:03:15.329048Z")

    @override_settings(TIME_FILTER_BUCKET_SECONDS=300)
    def test_bucket_size_comes_from_settings(self):
        request = _run("/api/ll/2.4.0/launches/?net__gt=2026-10-01T14:03:15Z&net__lt=2026-10-01T14:03:15Z")
        self.assertEqual(request.GET["net__gt"], "2026-10-01T14:00:00Z")
        self.assertEqual(request.GET["net__lt"], "2026-10-01T14:05:00Z")

    @override_settings(TIME_FILTER_BUCKET_SECONDS=0)
    def test_zero_bucket_turns_rounding_off(self):
        request = _run("/api/ll/2.4.0/launches/?net__gt=2026-10-01T14:03:15.329048Z")
        self.assertEqual(request.GET["net__gt"], "2026-10-01T14:03:15.329048Z")


class RoundTimeFiltersIntegrationTests(TestCase):
    def test_launch_list_accepts_rounded_filter(self):
        """The real LL filter must parse the rewritten value, or the apps get a 400."""
        response = self.client.get("/api/ll/2.4.0/launches/?limit=4&net__gt=2026-10-01T14:03:15.329048Z&ordering=net")
        self.assertEqual(response.status_code, 200, response.content[:500])
        self.assertEqual(response.wsgi_request.GET["net__gt"], "2026-10-01T14:03:00Z")
