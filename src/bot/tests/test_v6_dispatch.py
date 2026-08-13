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
        with mock.patch.object(self.handler, "_build_v5_data_payload", return_value=payload or PAYLOAD), \
             mock.patch("bot.app.notifications.v6.agency_group", return_value=agency), \
             mock.patch("bot.app.notifications.v6.location_group", return_value=location):
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

    def test_unmapped_agency_skips_strict_but_keeps_flexible(self):
        self._dispatch(agency=None)
        conditions = _conditions(self.handler.fcm)
        self.assertFalse([c for c in conditions if "_strict" in c])
        self.assertTrue([c for c in conditions if "_flex_" in c])
        self.assertTrue([c for c in conditions if "_all_" in c])

    def test_ios_sends_carry_the_unchanged_apns_config(self):
        self._dispatch()
        ios_calls = [c for c in self.handler.fcm.notify.call_args_list if c.kwargs.get("apns_config")]
        self.assertTrue(ios_calls)
        for call in ios_calls:
            headers = call.kwargs["apns_config"]["headers"]
            self.assertEqual(headers["apns-priority"], "10")
            self.assertEqual(headers["apns-collapse-id"], "uuid-123")
            self.assertEqual(call.kwargs["apns_config"]["payload"]["aps"]["mutable-content"], 1)

    def test_android_sends_are_data_only_with_collapse_key(self):
        self._dispatch()
        android_calls = [c for c in self.handler.fcm.notify.call_args_list if c.kwargs.get("android_config")]
        self.assertTrue(android_calls)
        for call in android_calls:
            self.assertIsNone(call.kwargs["notification_title"])
            self.assertEqual(call.kwargs["android_config"]["collapse_key"], "uuid-123")

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
