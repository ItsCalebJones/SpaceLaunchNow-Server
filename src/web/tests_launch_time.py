"""Tests for the shared launch-time display.

The precision -> display-shape mapping lives in Python precisely so it can be
covered here; launch-time.js is left with a single unconditional code path.
"""

from datetime import datetime
from datetime import timezone as dt_timezone

from django.template import Context, Template
from django.test import SimpleTestCase

from web.templatetags.sln_utils import SHAPE_DATE, SHAPE_DATETIME, launch_time_context


class _Precision:
    """Stand-in for a NetPrecision row; the tag only reads `.id`."""

    def __init__(self, precision_id):
        self.id = precision_id


NET = datetime(2026, 8, 14, 23, 32, 5, tzinfo=dt_timezone.utc)


class LaunchTimeContextTests(SimpleTestCase):
    def test_none_datetime_renders_nothing(self):
        self.assertEqual(launch_time_context(None), {"iso": None})

    def test_minute_precision_is_time_bearing_and_utc_labeled(self):
        ctx = launch_time_context(NET, _Precision(1))
        self.assertEqual(ctx["shape"], SHAPE_DATETIME)
        self.assertEqual(ctx["time_parts"], "hm")
        self.assertEqual(ctx["fallback"], "August 14, 2026 - 23:32 UTC")

    def test_second_precision_includes_seconds(self):
        ctx = launch_time_context(NET, _Precision(0))
        self.assertEqual(ctx["time_parts"], "hms")
        self.assertEqual(ctx["fallback"], "August 14, 2026 - 23:32:05 UTC")

    def test_hour_precision_is_prefixed_net_and_zeroed(self):
        ctx = launch_time_context(NET, _Precision(2))
        self.assertEqual(ctx["time_parts"], "h")
        self.assertEqual(ctx["prefix"], "NET")
        self.assertEqual(ctx["fallback"], "August 14, 2026 - NET 23:00 UTC")

    def test_naive_utc_conversion_from_other_offset(self):
        """A non-UTC aware datetime is normalised before rendering."""
        from datetime import timedelta

        eastern = dt_timezone(timedelta(hours=-4))
        ctx = launch_time_context(NET.astimezone(eastern), _Precision(1))
        self.assertEqual(ctx["fallback"], "August 14, 2026 - 23:32 UTC")
        self.assertTrue(ctx["iso"].endswith("+00:00"))

    def test_missing_precision_falls_back_to_minute(self):
        ctx = launch_time_context(NET, None)
        self.assertEqual(ctx["shape"], SHAPE_DATETIME)
        self.assertEqual(ctx["time_parts"], "hm")

    def test_coarse_precisions_carry_no_timezone_and_no_utc(self):
        """The core invariant: "Q3 2026" must not claim a timezone."""
        expected = {
            3: "Morning (local) August 14, 2026",
            4: "Afternoon (local) August 14, 2026",
            5: "August 14, 2026",
            6: "Week of August 14, 2026",
            7: "August 2026",
            8: "Q1 2026",
            9: "Q2 2026",
            10: "Q3 2026",
            11: "Q4 2026",
            12: "H1 2026",
            13: "H2 2026",
            14: "NET 2026",
            15: "FY 2026",
            16: "During the 2020s",
        }
        for precision_id, label in expected.items():
            with self.subTest(precision=precision_id):
                ctx = launch_time_context(NET, _Precision(precision_id))
                self.assertEqual(ctx["shape"], SHAPE_DATE)
                self.assertIsNone(ctx["time_parts"])
                self.assertEqual(ctx["fallback"], label)
                self.assertNotIn("UTC", ctx["fallback"])

    def test_every_precision_id_is_mapped(self):
        """All 17 documented precisions resolve to a known shape."""
        for precision_id in range(17):
            with self.subTest(precision=precision_id):
                ctx = launch_time_context(NET, _Precision(precision_id))
                self.assertIn(ctx["shape"], (SHAPE_DATE, SHAPE_DATETIME))
                self.assertTrue(ctx["fallback"])


class LaunchTimeTagTests(SimpleTestCase):
    def _render(self, value, precision=None):
        template = Template("{% load sln_utils %}{% launch_time value precision %}")
        return template.render(Context({"value": value, "precision": precision}))

    def test_time_bearing_markup_carries_iso_and_labeled_fallback(self):
        html = self._render(NET, _Precision(1))
        self.assertIn('datetime="2026-08-14T23:32:05+00:00"', html)
        self.assertIn('data-time-parts="hm"', html)
        self.assertIn("August 14, 2026 - 23:32 UTC", html)

    def test_coarse_markup_omits_time_parts(self):
        html = self._render(NET, _Precision(10))
        self.assertIn("Q3 2026", html)
        self.assertNotIn("data-time-parts", html)
        self.assertNotIn("UTC", html)

    def test_none_renders_empty(self):
        self.assertEqual(self._render(None).strip(), "")
