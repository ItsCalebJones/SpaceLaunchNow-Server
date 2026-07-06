"""Tests for the notification Prometheus counters.

Mirrors test_v5_notifications.py conventions: SimpleTestCase, handlers built
via __new__ to bypass NotificationService.__init__ (which needs FCM creds),
and self.fcm replaced with a mock — no database or live FCM required.

Counters are process-global, so every assertion is a before/after delta.
"""

from unittest import mock

from django.test import SimpleTestCase
from prometheus_client import REGISTRY

from bot.app.events.notification_handler import EventNotificationHandler
from bot.app.notifications import metrics
from bot.app.notifications.news_notification_handler import NewsNotificationHandler
from bot.app.notifications.notification_handler import NotificationHandler


def _attr(**kw):
    return type("Obj", (), kw)


def _sent(platform, category, result):
    return (
        REGISTRY.get_sample_value(
            "sln_notifications_sent_total",
            {"platform": platform, "category": category, "result": result},
        )
        or 0.0
    )


def _recipients(platform, category):
    return (
        REGISTRY.get_sample_value(
            "sln_notification_recipients_total",
            {"platform": platform, "category": category},
        )
        or 0.0
    )


# --------------------------------------------------------------------------- #
# 1. metrics module
# --------------------------------------------------------------------------- #
class RecordSendTests(SimpleTestCase):
    def test_success_increments_success_counter(self):
        before = _sent("android", "launch", "success")
        metrics.record_send(platform="android", category="launch", success=True)
        self.assertEqual(_sent("android", "launch", "success"), before + 1)

    def test_error_increments_error_counter(self):
        before = _sent("ios", "launch", "error")
        metrics.record_send(platform="ios", category="launch", success=False)
        self.assertEqual(_sent("ios", "launch", "error"), before + 1)

    def test_recipients_incremented_from_fcm_success_count(self):
        before = _recipients("android", "news")
        metrics.record_send(platform="android", category="news", success=True, result={"success": 3})
        self.assertEqual(_recipients("android", "news"), before + 3)

    def test_topic_response_without_count_does_not_move_recipients(self):
        before = _recipients("ios", "news")
        metrics.record_send(
            platform="ios",
            category="news",
            success=True,
            result={"name": "projects/sln/messages/abc"},
        )
        self.assertEqual(_recipients("ios", "news"), before)

    def test_error_does_not_move_recipients(self):
        before = _recipients("android", "event")
        metrics.record_send(platform="android", category="event", success=False, result={"success": 5})
        self.assertEqual(_recipients("android", "event"), before)

    def test_non_dict_result_is_safe(self):
        before = _sent("ios", "custom", "success")
        metrics.record_send(platform="ios", category="custom", success=True, result=None)
        metrics.record_send(platform="ios", category="custom", success=True, result="raw string")
        self.assertEqual(_sent("ios", "custom", "success"), before + 2)

    def test_extract_success_count(self):
        self.assertEqual(metrics._extract_success_count({"success": 4}), 4)
        self.assertEqual(metrics._extract_success_count({"success": "nope"}), 0)
        self.assertEqual(metrics._extract_success_count({"name": "projects/x"}), 0)
        self.assertEqual(metrics._extract_success_count(None), 0)


class StartMetricsServerTests(SimpleTestCase):
    def test_wraps_prometheus_start_http_server(self):
        with mock.patch.object(metrics, "start_http_server") as srv:
            metrics.start_metrics_server(9000)
        srv.assert_called_once_with(9000)


# --------------------------------------------------------------------------- #
# 2. launch path (V5NotificationMixin via NotificationHandler)
# --------------------------------------------------------------------------- #
class LaunchSendCounterTests(SimpleTestCase):
    def setUp(self):
        self.handler = NotificationHandler.__new__(NotificationHandler)
        self.handler.fcm = mock.Mock()
        self.data = {"notification_type": "tenMinutes", "launch_uuid": "uuid-1"}

    def test_android_success(self):
        self.handler.fcm.notify.return_value = {"name": "projects/sln/messages/1"}
        before = _sent("android", "launch", "success")
        result = self.handler.send_notif_v5_android(data=self.data, topics="'prod_v5_android' in topics")
        self.assertIsNone(result.error)
        self.assertEqual(_sent("android", "launch", "success"), before + 1)

    def test_android_error(self):
        self.handler.fcm.notify.side_effect = Exception("boom")
        before = _sent("android", "launch", "error")
        result = self.handler.send_notif_v5_android(data=self.data, topics="'prod_v5_android' in topics")
        self.assertIsNotNone(result.error)
        self.assertEqual(_sent("android", "launch", "error"), before + 1)

    def test_ios_success(self):
        self.handler.fcm.notify.return_value = {"name": "projects/sln/messages/2"}
        before = _sent("ios", "launch", "success")
        result = self.handler.send_notif_v5_ios(data=self.data, topics="'prod_v5_ios' in topics")
        self.assertIsNone(result.error)
        self.assertEqual(_sent("ios", "launch", "success"), before + 1)

    def test_ios_error(self):
        self.handler.fcm.notify.side_effect = Exception("boom")
        before = _sent("ios", "launch", "error")
        result = self.handler.send_notif_v5_ios(data=self.data, topics="'prod_v5_ios' in topics")
        self.assertIsNotNone(result.error)
        self.assertEqual(_sent("ios", "launch", "error"), before + 1)


# --------------------------------------------------------------------------- #
# 3. news path
# --------------------------------------------------------------------------- #
class NewsSendCounterTests(SimpleTestCase):
    def setUp(self):
        self.handler = NewsNotificationHandler.__new__(NewsNotificationHandler)
        self.handler.fcm = mock.Mock()
        self.handler.DEBUG = True
        self.article = _attr(
            id=1,
            news_site="SpaceNews",
            title="Title",
            link="https://example.com/a",
            featured_image="",
        )

    def test_success_increments_both_platforms(self):
        self.handler.fcm.notify.return_value = {"name": "projects/sln/messages/3"}
        before_android = _sent("android", "news", "success")
        before_ios = _sent("ios", "news", "success")
        self.handler._send_v5_notification(self.article)
        self.assertEqual(_sent("android", "news", "success"), before_android + 1)
        self.assertEqual(_sent("ios", "news", "success"), before_ios + 1)

    def test_error_increments_error_for_both_platforms(self):
        self.handler.fcm.notify.side_effect = Exception("boom")
        before_android = _sent("android", "news", "error")
        before_ios = _sent("ios", "news", "error")
        self.handler._send_v5_notification(self.article)
        self.assertEqual(_sent("android", "news", "error"), before_android + 1)
        self.assertEqual(_sent("ios", "news", "error"), before_ios + 1)


# --------------------------------------------------------------------------- #
# 4. event path
# --------------------------------------------------------------------------- #
EVENT_V5_DATA = {
    "notification_type": "event_notification",
    "title": "Event",
    "body": "Body",
    "event_id": "7",
}


class EventSendCounterTests(SimpleTestCase):
    def setUp(self):
        self.handler = EventNotificationHandler.__new__(EventNotificationHandler)
        self.handler.fcm = mock.Mock()
        self.handler.DEBUG = True

    def test_success_increments_both_platforms(self):
        self.handler.fcm.notify.return_value = {"name": "projects/sln/messages/4"}
        before_android = _sent("android", "event", "success")
        before_ios = _sent("ios", "event", "success")
        with mock.patch.object(EventNotificationHandler, "_build_v5_event_data", return_value=EVENT_V5_DATA):
            self.handler._send_v5_event_notification(_attr(), "event_notification")
        self.assertEqual(_sent("android", "event", "success"), before_android + 1)
        self.assertEqual(_sent("ios", "event", "success"), before_ios + 1)

    def test_error_increments_error_for_both_platforms(self):
        self.handler.fcm.notify.side_effect = Exception("boom")
        before_android = _sent("android", "event", "error")
        before_ios = _sent("ios", "event", "error")
        with mock.patch.object(EventNotificationHandler, "_build_v5_event_data", return_value=EVENT_V5_DATA):
            self.handler._send_v5_event_notification(_attr(), "event_notification")
        self.assertEqual(_sent("android", "event", "error"), before_android + 1)
        self.assertEqual(_sent("ios", "event", "error"), before_ios + 1)


# --------------------------------------------------------------------------- #
# 5. custom path
# --------------------------------------------------------------------------- #
CUSTOM_V5_DATA = {
    "notification_type": "custom",
    "title": "Announce",
    "body": "Body",
    "custom_id": "c1",
}


class CustomSendCounterTests(SimpleTestCase):
    def setUp(self):
        self.handler = NotificationHandler.__new__(NotificationHandler)
        self.handler.fcm = mock.Mock()
        self.handler.DEBUG = True

    def test_android_success_and_error(self):
        with mock.patch.object(NotificationHandler, "_build_v5_custom_data", return_value=CUSTOM_V5_DATA):
            self.handler.fcm.notify.return_value = {"name": "projects/sln/messages/5"}
            before = _sent("android", "custom", "success")
            self.handler._send_v5_custom_android(_attr())
            self.assertEqual(_sent("android", "custom", "success"), before + 1)

            self.handler.fcm.notify.side_effect = Exception("boom")
            before_err = _sent("android", "custom", "error")
            self.handler._send_v5_custom_android(_attr())
            self.assertEqual(_sent("android", "custom", "error"), before_err + 1)

    def test_ios_success_and_error(self):
        with mock.patch.object(NotificationHandler, "_build_v5_custom_data", return_value=CUSTOM_V5_DATA):
            self.handler.fcm.notify.return_value = {"name": "projects/sln/messages/6"}
            before = _sent("ios", "custom", "success")
            self.handler._send_v5_custom_ios(_attr())
            self.assertEqual(_sent("ios", "custom", "success"), before + 1)

            self.handler.fcm.notify.side_effect = Exception("boom")
            before_err = _sent("ios", "custom", "error")
            self.handler._send_v5_custom_ios(_attr())
            self.assertEqual(_sent("ios", "custom", "error"), before_err + 1)
