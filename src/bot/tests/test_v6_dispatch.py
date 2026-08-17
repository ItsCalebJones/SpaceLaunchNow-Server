"""Tests for V6 per-audience-class dispatch.

Test-only. The FCM client is mocked and every payload is stubbed; no DB, no FCM.
"""

import re
from unittest import mock

from django.test import SimpleTestCase

from bot.app.notifications.v6 import V6NotificationMixin, dual_send_v6_broadcast, send_v6_broadcast

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
# and send_v6 swallows the error into a counter -- so nothing but this test
# stands between an over-long label and a silent, total delivery failure.
ANALYTICS_LABEL_RE = re.compile(r"^[a-zA-Z0-9\-_.~%]{1,50}$")


class _Handler(V6NotificationMixin):
    """The launch path is all the mixin carries; broadcasts are free functions."""


def _conditions(fcm_mock) -> list[str]:
    return [call.kwargs["topic_condition"] for call in fcm_mock.notify.call_args_list]


def _analytics_labels(fcm_mock) -> list[str]:
    return [call.kwargs["fcm_options"]["analytics_label"] for call in fcm_mock.notify.call_args_list]


def _skip_calls(record_skip_mock) -> set[tuple[str, str, str]]:
    return {
        (call.kwargs["platform"], call.kwargs["audience_class"], call.kwargs["reason"])
        for call in record_skip_mock.call_args_list
    }


class LaunchDispatchTests(SimpleTestCase):
    def setUp(self):
        self.handler = _Handler()
        self.handler.fcm = mock.MagicMock()
        self.handler.DEBUG = False

    def _dispatch(self, payload=None, agency="spacex", location="florida", notification_type="oneHour"):
        with (
            mock.patch("bot.app.notifications.v6.agency_group", return_value=agency),
            mock.patch("bot.app.notifications.v6.location_group", return_value=location),
        ):
            return self.handler.send_v6_launch_notification(
                launch=mock.MagicMock(),
                notification_type=notification_type,
                data=payload or PAYLOAD,
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

    def test_a_webcastless_skip_is_recorded_so_the_volume_swing_is_explainable(self):
        # Without this, V6 send volume halves for a non-webcast launch with
        # nothing in metrics saying whether that is gating or a dispatch bug.
        payload = dict(PAYLOAD, webcast="False")
        with mock.patch("bot.app.notifications.v6.record_skip") as record_skip:
            self._dispatch(payload=payload)
        self.assertEqual(
            _skip_calls(record_skip),
            {
                (platform, audience_class, "no_webcast")
                for platform in ("android", "ios")
                for audience_class in ("all_w", "flex_w", "strict_w")
            },
        )

    def test_a_webcast_launch_records_no_skips(self):
        with mock.patch("bot.app.notifications.v6.record_skip") as record_skip:
            self._dispatch()
        record_skip.assert_not_called()

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
        skip_calls = _skip_calls(record_skip)
        self.assertIn(("android", "strict", "unmapped_agency"), skip_calls)
        self.assertIn(("ios", "strict", "unmapped_agency"), skip_calls)
        self.assertIn(("android", "strict_w", "unmapped_agency"), skip_calls)
        self.assertIn(("ios", "strict_w", "unmapped_agency"), skip_calls)

    def test_unmapped_location_records_skip_with_the_location_reason(self):
        with mock.patch("bot.app.notifications.v6.record_skip") as record_skip:
            self._dispatch(agency="spacex", location=None)
        skip_calls = _skip_calls(record_skip)
        self.assertIn(("android", "strict", "unmapped_location"), skip_calls)
        self.assertIn(("ios", "strict", "unmapped_location"), skip_calls)
        self.assertIn(("android", "strict_w", "unmapped_location"), skip_calls)
        self.assertIn(("ios", "strict_w", "unmapped_location"), skip_calls)

    def test_a_launch_missing_both_attributes_is_not_blamed_on_the_agency_table(self):
        with mock.patch("bot.app.notifications.v6.record_skip") as record_skip:
            self._dispatch(agency=None, location=None)
        reasons = {reason for _, _, reason in _skip_calls(record_skip)}
        self.assertEqual(reasons, {"unmapped_attributes"})

    def test_a_catch_all_agency_is_counted_as_a_group_table_gap(self):
        with mock.patch("bot.app.notifications.v6.record_group_fallback") as fallback:
            self._dispatch(agency="otherAgency", location="florida")
        fallback.assert_called_once_with("agency")

    def test_a_catch_all_location_is_counted_as_a_group_table_gap(self):
        with mock.patch("bot.app.notifications.v6.record_group_fallback") as fallback:
            self._dispatch(agency="spacex", location="unmappedLocation")
        fallback.assert_called_once_with("location")

    def test_a_fully_mapped_launch_records_no_group_fallback(self):
        with mock.patch("bot.app.notifications.v6.record_group_fallback") as fallback:
            self._dispatch()
        fallback.assert_not_called()

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

    def test_every_send_is_bounded_by_the_short_v6_timeout(self):
        # V6 adds up to 12 blocking calls to the single-threaded tracker loop;
        # V5's 240s here would make a stalled FCM delay the next launch's
        # oneMinute notification by tens of minutes.
        self._dispatch()
        for call in self.handler.fcm.notify.call_args_list:
            self.assertEqual(call.kwargs["timeout"], 30)

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
            results = self._dispatch(payload=payload, notification_type="definitely_not_a_type")
        self.assertEqual(results, [])
        self.handler.fcm.notify.assert_not_called()
        reasons = {reason for _, _, reason in _skip_calls(record_skip)}
        self.assertEqual(reasons, {"unknown_type"})
        self.assertEqual(len(record_skip.call_args_list), 12)


class AnalyticsLabelTests(SimpleTestCase):
    """FCM rejects an analytics_label over 50 chars with 400 INVALID_ARGUMENT,
    and send_v6 catches that into an error counter -- so an over-long label is
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

    def _dispatch_launch(self):
        with (
            mock.patch("bot.app.notifications.v6.agency_group", return_value="spacex"),
            mock.patch("bot.app.notifications.v6.location_group", return_value="florida"),
        ):
            self.handler.send_v6_launch_notification(launch=mock.MagicMock(), notification_type="oneHour", data=PAYLOAD)

    def test_every_launch_class_label_is_within_the_fcm_limit(self):
        self._dispatch_launch()
        # 6 classes x 2 platforms, the full matrix for a webcast launch.
        self._assert_labels_valid(_analytics_labels(self.handler.fcm), 12)

    def test_launch_labels_are_unique_per_class(self):
        # Dropping the platform segment must not collapse two sends onto one
        # label: the class still distinguishes them, and platform is carried by
        # the condition, the topic names, and the `platform` metric label.
        self._dispatch_launch()
        self.assertEqual(len(set(_analytics_labels(self.handler.fcm))), 6)

    def test_every_broadcast_label_is_within_the_fcm_limit(self):
        # Realistic collapse ids: event/article/notification PKs are integers.
        for kind, collapse_id in (
            ("events", "event_4294967295"),
            ("news", "news_4294967295"),
            ("announce", "custom_4294967295"),
        ):
            with self.subTest(kind=kind):
                self.handler.fcm.reset_mock()
                send_v6_broadcast(
                    self.handler.fcm,
                    debug=False,
                    kind=kind,
                    data={"notification_type": "custom", "title": "t", "body": "b"},
                    collapse_id=collapse_id,
                    category="custom",
                )
                self._assert_labels_valid(_analytics_labels(self.handler.fcm), 2)


class BroadcastDispatchTests(SimpleTestCase):
    def setUp(self):
        self.fcm = mock.MagicMock()

    def test_broadcast_emits_one_condition_per_platform(self):
        send_v6_broadcast(
            self.fcm,
            debug=False,
            kind="events",
            data={"notification_type": "event_notification", "title": "t", "body": "b", "event_id": "999"},
            collapse_id="event_999",
            category="event",
        )
        self.assertEqual(
            sorted(_conditions(self.fcm)),
            ["'v6_prod_android_events' in topics", "'v6_prod_ios_events' in topics"],
        )

    def test_broadcast_can_be_narrowed_to_one_platform(self):
        send_v6_broadcast(
            self.fcm,
            debug=False,
            kind="announce",
            data={"notification_type": "custom", "title": "t", "body": "b", "custom_id": "1"},
            collapse_id="custom_1",
            category="custom",
            platforms=("ios",),
        )
        self.assertEqual(_conditions(self.fcm), ["'v6_prod_ios_announce' in topics"])

    def test_title_and_body_come_from_the_payload(self):
        # They used to be passed separately alongside the same dict, which only
        # created a way for the alert and the payload to disagree.
        send_v6_broadcast(
            self.fcm,
            debug=False,
            kind="news",
            data={"notification_type": "featured_news", "title": "Headline", "body": "Story", "article_id": "1"},
            collapse_id="news_1",
            category="news",
            platforms=("ios",),
        )
        call = self.fcm.notify.call_args
        self.assertEqual(call.kwargs["notification_title"], "Headline")
        self.assertEqual(call.kwargs["notification_body"], "Story")

    def test_an_unknown_kind_raises_before_any_send(self):
        with self.assertRaises(ValueError):
            send_v6_broadcast(
                self.fcm,
                debug=False,
                kind="announcements",
                data={"notification_type": "custom", "title": "t", "body": "b"},
                collapse_id="custom_1",
                category="custom",
            )
        self.fcm.notify.assert_not_called()

    def test_dual_send_contains_an_unknown_kind_instead_of_raising(self):
        # The containment wrapper is what every V5 path calls, so a bad kind
        # must surface in logs without aborting the V5 send that preceded it.
        dual_send_v6_broadcast(
            self.fcm,
            debug=False,
            kind="announcements",
            data={"notification_type": "custom", "title": "t", "body": "b"},
            collapse_id="custom_1",
            category="custom",
        )
        self.fcm.notify.assert_not_called()

    def test_dual_send_contains_a_failing_send(self):
        self.fcm.notify.side_effect = Exception("boom")
        dual_send_v6_broadcast(
            self.fcm,
            debug=False,
            kind="news",
            data={"notification_type": "featured_news", "title": "t", "body": "b"},
            collapse_id="news_1",
            category="news",
        )


class DualSendTests(SimpleTestCase):
    """The V5 broadcast must keep firing alongside V6 for shipped clients."""

    def setUp(self):
        from bot.app.notifications.notification_handler import NotificationHandler

        self.handler = NotificationHandler.__new__(NotificationHandler)
        self.handler.fcm = mock.MagicMock()
        self.handler.DEBUG = False

    def _send(self, notify_discord):
        launch = mock.MagicMock()
        with (
            mock.patch.object(self.handler, "_build_v5_data_payload", return_value=PAYLOAD) as build,
            mock.patch.object(self.handler, "notify_discord", notify_discord),
            mock.patch("bot.app.notifications.v6.agency_group", return_value="spacex"),
            mock.patch("bot.app.notifications.v6.location_group", return_value="florida"),
        ):
            self.handler.send_v3_notification(launch, "oneHour", "Launch attempt in one hour.")
        return build

    def test_v5_broadcast_and_v6_conditions_both_fire(self):
        self._send(mock.MagicMock())
        conditions = _conditions(self.handler.fcm)
        v5 = [c for c in conditions if "prod_v5_" in c]
        v6 = [c for c in conditions if "v6_prod_" in c]
        self.assertEqual(len(v5), 2, "V5 android + ios broadcast must still fire")
        self.assertEqual(len(v6), 12, "V6 must emit 6 classes x 2 platforms for a webcast launch")

    def test_the_v5_payload_is_built_once_for_both_schemes(self):
        # V6 ships the same payload shape; rebuilding it repeats every ORM
        # traversal (vid_urls, program, rocket families, image FKs) per launch.
        build = self._send(mock.MagicMock())
        self.assertEqual(build.call_count, 1)

    def test_a_failing_v6_dispatch_still_leaves_discord_notified(self):
        # notify_discord is sequenced before V6 precisely so a V6 failure cannot
        # suppress it. Without both the ordering and the try/except, removing
        # either one silently drops the Discord post on every V6 error.
        notify_discord = mock.MagicMock()
        with mock.patch.object(type(self.handler), "send_v6_launch_notification", side_effect=Exception("boom")):
            self._send(notify_discord)
        notify_discord.assert_called_once()

    def test_a_failing_v6_dispatch_does_not_propagate(self):
        with mock.patch.object(type(self.handler), "send_v6_launch_notification", side_effect=Exception("boom")):
            self._send(mock.MagicMock())
        # Reaching here without an exception is the assertion; the V5 sends
        # above it must also have completed.
        self.assertEqual(len([c for c in _conditions(self.handler.fcm) if "prod_v5_" in c]), 2)


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

        # No composite class needed: broadcasts are free functions, so this
        # mixin no longer has a hidden dependency on another mixin's presence.
        handler = CustomNotificationMixin()
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

    def test_a_failing_v6_broadcast_still_leaves_the_v5_custom_send_done(self):
        # check_custom marks send_ios_complete immediately after this call with
        # no try/except of its own; a raising V6 send would leave the record
        # queued and the V5 custom notification would be sent again next cycle.
        handler = self._custom_handler()
        v5 = {"notification_type": "custom", "title": "t", "body": "b", "custom_id": "cust-1"}
        with (
            mock.patch.object(handler, "_build_v5_custom_data", return_value=v5),
            mock.patch("bot.app.notifications.v6.send_v6_broadcast", side_effect=Exception("boom")),
        ):
            handler._send_v5_custom_ios(pending=object())
            handler._send_v5_custom_android(pending=object())
        # The V5 sends must have gone out despite every V6 attempt failing.
        v5_conditions = [c for c in _conditions(handler.fcm) if "v5_" in c]
        self.assertEqual(len(v5_conditions), 2)
        self.assertEqual(self._v6_conditions(handler.fcm), [])
