"""Tests for scripts/fcm_delivery_snapshot.py (parsing and ratio math).

Test-only. Uses a recorded, trimmed deliveryData response (UUIDs shortened); no
live FCM call and no gcloud. Runs under the Django test runner.
"""

import importlib.util
import sys
from datetime import date
from pathlib import Path

from django.test import SimpleTestCase

_SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "fcm_delivery_snapshot.py"
_spec = importlib.util.spec_from_file_location("fcm_delivery_snapshot", _SCRIPT)
snap = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = snap  # dataclasses looks the module up by name
_spec.loader.exec_module(snap)

APP = "1:610310574961:android:4553f5c8ecd77279"


def _row(day, label, count=None, lowered=None):
    data = {}
    if count is not None:
        data["countMessagesAccepted"] = str(count)  # the API returns int64 as a string
    if lowered is not None:
        data["messageInsightPercents"] = {"priorityLowered": lowered}
    row = {"appId": APP, "date": {"year": 2026, "month": 11, "day": day}, "data": data}
    if label:
        row["analyticsLabel"] = label
    return row


# Recorded shape: 11-12 has two launches; 11-13 is an empty day (no label);
# 11-15 has a broadcast pair; webcast classes come back `data: {}`.
SAMPLE = [
    _row(12, "v5_android_aaaa", 8600, lowered=7),
    _row(12, "v6_all_aaaa", 5500),
    _row(12, "v6_flex_aaaa", 4400),
    _row(12, "v6_strict_aaaa", 800),
    _row(12, "v6_all_w_aaaa"),
    _row(12, "v6_flex_w_aaaa"),
    _row(12, "v6_strict_w_aaaa"),
    _row(12, "v5_android_bbbb", 8400, lowered=5),
    _row(12, "v6_all_bbbb", 5000),
    _row(13, None),
    _row(15, "v5_android_event_42", 100),
    _row(15, "v6_android_event_42", 3000),
    _row(15, "v6_all_orphan", 9999),  # no V5 leg: must not count
]


class ClassifyLabelTests(SimpleTestCase):
    def test_v5_launch_and_broadcast(self):
        self.assertEqual(snap.classify_label("v5_android_aaaa"), ("v5", "aaaa"))
        self.assertEqual(snap.classify_label("v5_android_event_42"), ("v5", "event_42"))

    def test_v6_classes_share_the_send_key(self):
        for label in ("v6_all_aaaa", "v6_flex_aaaa", "v6_strict_aaaa", "v6_all_w_aaaa", "v6_strict_w_aaaa"):
            self.assertEqual(snap.classify_label(label), ("v6", "aaaa"), label)

    def test_v6_broadcast_matches_v5_key(self):
        self.assertEqual(snap.classify_label("v6_android_event_42"), ("v6", "event_42"))

    def test_other_labels_are_ignored(self):
        for label in ("v5_ios_aaaa", "v6_ios_event_42", "something_else"):
            self.assertIsNone(snap.classify_label(label), label)


class AggregateTests(SimpleTestCase):
    def setUp(self):
        self.days = {s.day: s for s in snap.aggregate(SAMPLE)}

    def test_empty_day_is_skipped(self):
        self.assertNotIn(date(2026, 11, 13), self.days)
        self.assertEqual(sorted(self.days), [date(2026, 11, 12), date(2026, 11, 15)])

    def test_counts_sum_over_labels_and_string_ints(self):
        day = self.days[date(2026, 11, 12)]
        self.assertEqual(day.v5, 17000)
        self.assertEqual(day.v6, 5500 + 4400 + 800 + 5000)
        self.assertEqual(day.paired_sends, 2)

    def test_empty_v6_labels_count_as_zero_and_are_reported(self):
        self.assertEqual(self.days[date(2026, 11, 12)].empty_v6_labels, 3)

    def test_ratio_and_gate(self):
        day = self.days[date(2026, 11, 15)]
        self.assertAlmostEqual(day.ratio, 100 / 3000)
        self.assertTrue(day.passes)
        self.assertFalse(self.days[date(2026, 11, 12)].passes)

    def test_orphan_v6_send_does_not_inflate_denominator(self):
        self.assertEqual(self.days[date(2026, 11, 15)].v6, 3000)

    def test_priority_lowered_is_weighted_by_v5_count(self):
        expected = (7 * 8600 + 5 * 8400) / 17000
        self.assertAlmostEqual(self.days[date(2026, 11, 12)].v5_priority_lowered, expected)
        self.assertIsNone(self.days[date(2026, 11, 15)].v5_priority_lowered)

    def test_zero_v6_gives_no_ratio(self):
        days = snap.aggregate([_row(1, "v5_android_x", 10)])
        self.assertIsNone(days[0].ratio)
        self.assertFalse(days[0].passes)


class StreakTests(SimpleTestCase):
    def _days(self, spec):
        rows = []
        for day, v5 in spec:
            rows += [_row(day, f"v5_android_s{day}", v5), _row(day, f"v6_all_s{day}", 1000)]
        return snap.aggregate(rows)

    def test_streak_counts_consecutive_passing_days_at_the_end(self):
        self.assertEqual(snap.trailing_pass_streak(self._days([(1, 500), (2, 10), (3, 20), (4, 30)])), 3)

    def test_gap_in_days_breaks_the_streak(self):
        self.assertEqual(snap.trailing_pass_streak(self._days([(1, 10), (2, 10), (4, 10)])), 1)

    def test_failing_last_day_gives_zero(self):
        self.assertEqual(snap.trailing_pass_streak(self._days([(1, 10), (2, 900)])), 0)

    def test_boundary_five_percent_passes(self):
        self.assertEqual(snap.trailing_pass_streak(self._days([(1, 50)])), 1)


class ReportTests(SimpleTestCase):
    def test_report_states_gate_not_met(self):
        report = snap.format_report(snap.aggregate(SAMPLE))
        self.assertIn("NOT MET", report)
        self.assertIn("2026-11-15", report)

    def test_markdown_row_has_one_cell_per_header_column(self):
        row = snap.markdown_row(snap.aggregate(SAMPLE), date(2026, 11, 23))
        header = snap.MARKDOWN_HEADER.splitlines()[0]
        self.assertEqual(row.count("|"), header.count("|"))
        self.assertIn("2026-11-12 to 2026-11-15 (2 d)", row)

    def test_markdown_row_without_data(self):
        self.assertIn("no data", snap.markdown_row([], date(2026, 11, 23)))
