"""Tests for V6 per-audience-class dispatch.

Test-only. self.fcm is mocked and every payload is stubbed; no DB, no FCM.
"""

import re
from unittest import mock

from django.test import SimpleTestCase

from bot.app.notifications.v5 import V5NotificationMixin
from bot.app.notifications.v6 import V6NotificationMixin

# A real launch UUID, not a short placeholder: launch_uuid is the longest
# component of the launch analytics label and 36 chars is what production sends.
LAUNCH_UUID = "b2a0e2a4-4d1e-4e6b-9a1f-3c7d5e8f0a12"

PAYLOAD = {
    "notification_type": "oneHour",
    "launch_uuid": LAUNCH_UUID,
    "title": "Falcon 9",
    "body": "Launch attempt in one hour.",
    "webcast": "True",
}

# FcmOptions.analytics_label, per the FCM v1 API: 1-50 chars from this set.
# Violations are rejected with 400 INVALID_ARGUMENT; pyfcm does not validate,
# and _send_v6 swallows the error into a counter -- so nothing but this test
# stands between an over-long label and a silent, total delivery failure.
ANALYTICS_LABEL_RE = re.compile(r"^[a-zA-Z0-9\-_.~%]{1,50}$")


class _Handler(V6NotificationMixin, V5NotificationMixin):
    """The production handler composes both mixins; mirror that here."""


def _conditions(fcm_mock) -> list[str]:
    return [call.kwargs["topic_condition"] for call in fcm_mock.notify.call_args_list]


def _analytics_labels(fcm_mock) -> list[str]:
    return [call.kwargs["fcm_options"]["analytics_label"] for call in fcm_mock.notify.call_args_list]


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
            self.assertEqual(headers["apns-collapse-id"], LAUNCH_UUID)
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
            self.assertEqual(call.kwargs["android_config"]["collapse_key"], LAUNCH_UUID)
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

    def test_an_unknown_notification_type_skips_every_class(self):
        with mock.patch("bot.app.notifications.v6.record_skip") as record_skip:
            payload = dict(PAYLOAD, notification_type="definitely_not_a_type")
            with (
                mock.patch.object(self.handler, "_build_v5_data_payload", return_value=payload),
                mock.patch("bot.app.notifications.v6.agency_group", return_value="spacex"),
                mock.patch("bot.app.notifications.v6.location_group", return_value="florida"),
            ):
                results = self.handler.send_v6_launch_notification(
                    launch=mock.MagicMock(),
                    notification_type="definitely_not_a_type",
                    contents="c",
                )
        self.assertEqual(results, [])
        self.handler.fcm.notify.assert_not_called()
        reasons = {call.kwargs["reason"] for call in record_skip.call_args_list}
        self.assertEqual(reasons, {"unknown_type"})
        self.assertEqual(len(record_skip.call_args_list), 12)


class AnalyticsLabelTests(SimpleTestCase):
    """FCM rejects an analytics_label over 50 chars with 400 INVALID_ARGUMENT,
    and _send_v6 catches that into an error counter -- so an over-long label is
    a silent, total delivery failure for every class it applies to. Same class
    of latent failure as an over-budget condition; same permanence of guard."""

    def setUp(self):
        self.handler = _Handler()
        self.handler.fcm = mock.MagicMock()
        self.handler.DEBUG = False

    def _assert_labels_valid(self, labels, expected_count):
        self.assertEqual(len(labels), expected_count)
        for label in labels:
            self.assertRegex(label, ANALYTICS_LABEL_RE, msg=f"{label!r} is {len(label)} chars")

    def test_every_launch_class_label_is_within_the_fcm_limit(self):
        with (
            mock.patch.object(self.handler, "_build_v5_data_payload", return_value=PAYLOAD),
            mock.patch("bot.app.notifications.v6.agency_group", return_value="spacex"),
            mock.patch("bot.app.notifications.v6.location_group", return_value="florida"),
        ):
            self.handler.send_v6_launch_notification(launch=mock.MagicMock(), notification_type="oneHour", contents="c")
        # 6 classes x 2 platforms, the full matrix for a webcast launch.
        self._assert_labels_valid(_analytics_labels(self.handler.fcm), 12)

    def test_launch_labels_are_unique_per_class(self):
        # Dropping the platform segment must not collapse two sends onto one
        # label: the class still distinguishes them, and platform is carried by
        # the condition, the topic names, and the `platform` metric label.
        with (
            mock.patch.object(self.handler, "_build_v5_data_payload", return_value=PAYLOAD),
            mock.patch("bot.app.notifications.v6.agency_group", return_value="spacex"),
            mock.patch("bot.app.notifications.v6.location_group", return_value="florida"),
        ):
            self.handler.send_v6_launch_notification(launch=mock.MagicMock(), notification_type="oneHour", contents="c")
        labels = _analytics_labels(self.handler.fcm)
        self.assertEqual(len(set(labels)), 6)

    def test_every_broadcast_label_is_within_the_fcm_limit(self):
        # Realistic collapse ids: event/article/notification PKs are integers.
        for kind, collapse_id in (
            ("events", "event_4294967295"),
            ("news", "news_4294967295"),
            ("announce", "custom_4294967295"),
        ):
            with self.subTest(kind=kind):
                self.handler.fcm.reset_mock()
                self.handler.send_v6_broadcast(
                    kind=kind,
                    v5_data={"notification_type": "custom"},
                    title="t",
                    body="b",
                    collapse_id=collapse_id,
                    category="custom",
                )
                self._assert_labels_valid(_analytics_labels(self.handler.fcm), 2)


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

    def test_broadcast_can_be_narrowed_to_one_platform(self):
        self.handler.send_v6_broadcast(
            kind="announce",
            v5_data={"notification_type": "custom", "custom_id": "1"},
            title="t",
            body="b",
            collapse_id="custom_1",
            category="custom",
            platforms=("ios",),
        )
        self.assertEqual(_conditions(self.handler.fcm), ["'v6_prod_ios_announce' in topics"])


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


class BroadcastWiringTests(SimpleTestCase):
    def _v6_conditions(self, fcm_mock):
        return [c for c in _conditions(fcm_mock) if "v6_prod_" in c]

    def test_event_send_also_targets_the_v6_event_topics(self):
        from bot.app.events.notification_handler import EventNotificationHandler

        handler = EventNotificationHandler.__new__(EventNotificationHandler)
        handler.fcm = mock.MagicMock()
        handler.DEBUG = False
        v5 = {"notification_type": "event_notification", "title": "t", "body": "b", "event_id": "999"}
        with mock.patch.object(handler, "_build_v5_event_data", return_value=v5):
            handler._send_v5_event_notification(event=object(), event_type="event")
        self.assertEqual(
            sorted(self._v6_conditions(handler.fcm)),
            ["'v6_prod_android_events' in topics", "'v6_prod_ios_events' in topics"],
        )

    def test_news_send_also_targets_the_v6_news_topics(self):
        from bot.app.notifications.news_notification_handler import NewsNotificationHandler

        handler = NewsNotificationHandler.__new__(NewsNotificationHandler)
        handler.fcm = mock.MagicMock()
        handler.DEBUG = False
        v5 = {"notification_type": "featured_news", "title": "t", "body": "b", "article_id": "777"}
        with mock.patch.object(handler, "_build_v5_news_data", return_value=v5):
            handler._send_v5_notification(article=object())
        self.assertEqual(
            sorted(self._v6_conditions(handler.fcm)),
            ["'v6_prod_android_news' in topics", "'v6_prod_ios_news' in topics"],
        )

    def _custom_handler(self):
        from bot.app.notifications.custom import CustomNotificationMixin
        from bot.app.notifications.v6 import V6NotificationMixin

        class _Custom(CustomNotificationMixin, V6NotificationMixin):
            pass

        handler = _Custom()
        handler.fcm = mock.MagicMock()
        handler.DEBUG = False
        return handler

    def test_custom_ios_send_targets_only_the_ios_announce_topic(self):
        # Notification.send_ios / send_android are independent, and check_custom
        # drives a separate queryset from each. Emitting both platforms from the
        # iOS method would push announcements to Android users an admin
        # deliberately excluded.
        handler = self._custom_handler()
        v5 = {"notification_type": "custom", "title": "t", "body": "b", "custom_id": "cust-1"}
        with mock.patch.object(handler, "_build_v5_custom_data", return_value=v5):
            handler._send_v5_custom_ios(pending=object())
        self.assertEqual(self._v6_conditions(handler.fcm), ["'v6_prod_ios_announce' in topics"])

    def test_custom_android_send_targets_only_the_android_announce_topic(self):
        # Without this call an admin sending Android-only reaches nobody on V6.
        handler = self._custom_handler()
        v5 = {"notification_type": "custom", "title": "t", "body": "b", "custom_id": "cust-1"}
        with mock.patch.object(handler, "_build_v5_custom_data", return_value=v5):
            handler._send_v5_custom_android(pending=object())
        self.assertEqual(self._v6_conditions(handler.fcm), ["'v6_prod_android_announce' in topics"])

    def test_a_custom_send_for_both_platforms_emits_each_topic_once(self):
        handler = self._custom_handler()
        v5 = {"notification_type": "custom", "title": "t", "body": "b", "custom_id": "cust-1"}
        with mock.patch.object(handler, "_build_v5_custom_data", return_value=v5):
            handler._send_v5_custom_ios(pending=object())
            handler._send_v5_custom_android(pending=object())
        self.assertEqual(
            sorted(self._v6_conditions(handler.fcm)),
            ["'v6_prod_android_announce' in topics", "'v6_prod_ios_announce' in topics"],
        )

    def test_a_failing_v6_broadcast_does_not_propagate_into_the_v5_flow(self):
        # check_custom marks send_ios_complete immediately after this call with
        # no try/except of its own; a raising V6 send would leave the record
        # queued and the V5 custom notification would be sent again next cycle.
        handler = self._custom_handler()
        v5 = {"notification_type": "custom", "title": "t", "body": "b", "custom_id": "cust-1"}
        with (
            mock.patch.object(handler, "_build_v5_custom_data", return_value=v5),
            mock.patch.object(handler, "send_v6_broadcast", side_effect=Exception("boom")),
        ):
            handler._send_v5_custom_ios(pending=object())
            handler._send_v5_custom_android(pending=object())
