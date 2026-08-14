"""Tests for V6 per-audience-class dispatch.

Test-only. self.fcm is mocked and every payload is stubbed; no DB, no FCM.
"""

from unittest import mock

from django.test import SimpleTestCase

from bot.app.notifications.v5 import V5NotificationMixin
from bot.app.notifications.v6 import V6NotificationMixin

PAYLOAD = {
    "notification_type": "oneHour",
    "launch_uuid": "uuid-123",
    "title": "Falcon 9",
    "body": "Launch attempt in one hour.",
    "webcast": "True",
}


class _Handler(V6NotificationMixin, V5NotificationMixin):
    """The production handler composes both mixins; mirror that here."""


def _conditions(fcm_mock) -> list[str]:
    return [call.kwargs["topic_condition"] for call in fcm_mock.notify.call_args_list]


class LaunchDispatchTests(SimpleTestCase):
    def setUp(self):
        self.handler = _Handler()
        self.handler.fcm = mock.MagicMock()
        self.handler.DEBUG = False

    def _dispatch(self, payload=None, agency="spacex", location="florida"):
        with (
            mock.patch.object(self.handler, "_build_v5_data_payload", return_value=payload or PAYLOAD),
            mock.patch("bot.app.notifications.v6.agency_group", return_value=agency),
            mock.patch("bot.app.notifications.v6.location_group", return_value=location),
        ):
            return self.handler.send_v6_launch_notification(
                launch=mock.MagicMock(), notification_type="oneHour", contents="Launch attempt in one hour."
            )

    def test_webcast_launch_targets_all_six_classes_on_both_platforms(self):
        self._dispatch()
        self.assertEqual(len(_conditions(self.handler.fcm)), 12)

    def test_non_webcast_launch_skips_the_webcast_only_classes(self):
        payload = dict(PAYLOAD, webcast="False")
        self._dispatch(payload=payload)
        conditions = _conditions(self.handler.fcm)
        self.assertEqual(len(conditions), 6)
        self.assertFalse([c for c in conditions if "_w_" in c])

    def test_each_condition_is_emitted_exactly_once(self):
        self._dispatch()
        conditions = _conditions(self.handler.fcm)
        self.assertEqual(len(conditions), len(set(conditions)))

    def test_strict_condition_is_exactly_pinned(self):
        # A substring check alone tolerates a swapped agency/location argument
        # or a hardcoded notification_type; only the full, ordered string rules
        # those out.
        self._dispatch()
        conditions = _conditions(self.handler.fcm)
        self.assertIn(
            "'v6_prod_ios_strict_oneHour' in topics && 'v6_prod_spacex' in topics && 'v6_prod_florida' in topics",
            conditions,
        )

    def test_unmapped_agency_skips_strict_but_keeps_flexible(self):
        self._dispatch(agency=None)
        conditions = _conditions(self.handler.fcm)
        self.assertFalse([c for c in conditions if "_strict" in c])
        self.assertTrue([c for c in conditions if "_flex_" in c])
        self.assertTrue([c for c in conditions if "_all_" in c])

    def test_unmapped_agency_records_skip_with_the_agency_reason(self):
        with mock.patch("bot.app.notifications.v6.record_skip") as record_skip:
            self._dispatch(agency=None, location="china")
        skip_calls = {
            (call.kwargs["platform"], call.kwargs["audience_class"], call.kwargs["reason"])
            for call in record_skip.call_args_list
        }
        self.assertIn(("android", "strict", "unmapped_agency"), skip_calls)
        self.assertIn(("ios", "strict", "unmapped_agency"), skip_calls)
        self.assertIn(("android", "strict_w", "unmapped_agency"), skip_calls)
        self.assertIn(("ios", "strict_w", "unmapped_agency"), skip_calls)

    def test_unmapped_location_records_skip_with_the_location_reason(self):
        with mock.patch("bot.app.notifications.v6.record_skip") as record_skip:
            self._dispatch(agency="spacex", location=None)
        skip_calls = {
            (call.kwargs["platform"], call.kwargs["audience_class"], call.kwargs["reason"])
            for call in record_skip.call_args_list
        }
        self.assertIn(("android", "strict", "unmapped_location"), skip_calls)
        self.assertIn(("ios", "strict", "unmapped_location"), skip_calls)
        self.assertIn(("android", "strict_w", "unmapped_location"), skip_calls)
        self.assertIn(("ios", "strict_w", "unmapped_location"), skip_calls)

    def test_ios_sends_carry_the_unchanged_apns_config(self):
        self._dispatch()
        ios_calls = [c for c in self.handler.fcm.notify.call_args_list if c.kwargs.get("apns_config")]
        self.assertEqual(len(ios_calls), 6)
        for call in ios_calls:
            headers = call.kwargs["apns_config"]["headers"]
            self.assertEqual(headers["apns-priority"], "10")
            self.assertEqual(headers["apns-collapse-id"], "uuid-123")
            self.assertEqual(call.kwargs["apns_config"]["payload"]["aps"]["mutable-content"], 1)
            self.assertEqual(call.kwargs["notification_title"], PAYLOAD["title"])
            self.assertEqual(call.kwargs["notification_body"], PAYLOAD["body"])

    def test_android_sends_are_data_only_with_collapse_key(self):
        self._dispatch()
        android_calls = [c for c in self.handler.fcm.notify.call_args_list if c.kwargs.get("android_config")]
        self.assertEqual(len(android_calls), 6)
        for call in android_calls:
            self.assertIsNone(call.kwargs["notification_title"])
            self.assertIsNone(call.kwargs["notification_body"])
            self.assertEqual(call.kwargs["android_config"]["collapse_key"], "uuid-123")
            self.assertEqual(call.kwargs["android_config"]["priority"], "high")
            self.assertEqual(call.kwargs["android_config"]["ttl"], "86400s")

    def test_prod_env_appears_in_topic_names_when_debug_is_false(self):
        self._dispatch()
        for condition in _conditions(self.handler.fcm):
            self.assertIn("v6_prod_", condition)

    def test_debug_env_appears_in_topic_names_when_debug_is_true(self):
        self.handler.DEBUG = True
        self._dispatch()
        for condition in _conditions(self.handler.fcm):
            self.assertIn("v6_debug_", condition)

    def test_a_failing_send_does_not_abort_the_remaining_classes(self):
        self.handler.fcm.notify.side_effect = [Exception("boom")] + [None] * 11
        results = self._dispatch()
        self.assertEqual(len(results), 12)
        self.assertEqual(len([r for r in results if r.error is not None]), 1)


class BroadcastDispatchTests(SimpleTestCase):
    def setUp(self):
        self.handler = _Handler()
        self.handler.fcm = mock.MagicMock()
        self.handler.DEBUG = False

    def test_broadcast_emits_one_condition_per_platform(self):
        self.handler.send_v6_broadcast(
            kind="events",
            v5_data={"notification_type": "event_notification", "event_id": "999"},
            title="t",
            body="b",
            collapse_id="event_999",
            category="event",
        )
        conditions = _conditions(self.handler.fcm)
        self.assertEqual(
            sorted(conditions),
            ["'v6_prod_android_events' in topics", "'v6_prod_ios_events' in topics"],
        )


class DualSendTests(SimpleTestCase):
    """The V5 broadcast must keep firing alongside V6 for shipped clients."""

    def setUp(self):
        from bot.app.notifications.notification_handler import NotificationHandler

        self.handler = NotificationHandler.__new__(NotificationHandler)
        self.handler.fcm = mock.MagicMock()
        self.handler.DEBUG = False

    def test_v5_broadcast_and_v6_conditions_both_fire(self):
        launch = mock.MagicMock()
        with (
            mock.patch.object(self.handler, "_build_v5_data_payload", return_value=PAYLOAD),
            mock.patch.object(self.handler, "notify_discord"),
            mock.patch("bot.app.notifications.v6.agency_group", return_value="spacex"),
            mock.patch("bot.app.notifications.v6.location_group", return_value="florida"),
        ):
            self.handler.send_v3_notification(launch, "oneHour", "Launch attempt in one hour.")

        conditions = _conditions(self.handler.fcm)
        v5 = [c for c in conditions if "prod_v5_" in c]
        v6 = [c for c in conditions if "v6_prod_" in c]
        self.assertEqual(len(v5), 2, "V5 android + ios broadcast must still fire")
        self.assertEqual(len(v6), 12, "V6 must emit 6 classes x 2 platforms for a webcast launch")
