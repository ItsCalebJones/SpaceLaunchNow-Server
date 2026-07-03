"""Tests that every V5 iOS push sets apns-collapse-id to the per-entity key.

Test-only. Each test mocks self.fcm and inspects the apns_config headers of the
iOS notify() call. No DB, no live FCM. Runs under the Django test runner.
"""

from unittest import mock

from django.test import SimpleTestCase

from bot.app.events.notification_handler import EventNotificationHandler
from bot.app.notifications.custom import CustomNotificationMixin
from bot.app.notifications.news_notification_handler import NewsNotificationHandler
from bot.app.notifications.v5 import V5NotificationMixin


def _ios_apns_headers(fcm_mock) -> dict:
    """Return the apns_config['headers'] dict from the iOS notify() call.

    The combined send methods call fcm.notify twice (Android then iOS); only the
    iOS call passes apns_config, so we select that one.
    """
    for call in fcm_mock.notify.call_args_list:
        apns = call.kwargs.get("apns_config")
        if apns:
            return apns["headers"]
    raise AssertionError("no iOS notify() call with apns_config was made")


class LaunchCollapseIdTests(SimpleTestCase):
    def setUp(self):
        self.mixin = V5NotificationMixin()
        self.mixin.fcm = mock.MagicMock()
        self.mixin.DEBUG = True

    def test_ios_sets_apns_collapse_id_to_launch_uuid(self):
        data = {"notification_type": "oneHour", "launch_uuid": "uuid-123"}
        self.mixin.send_notif_v5_ios(data=data, topics="'prod_v5_ios' in topics")
        headers = _ios_apns_headers(self.mixin.fcm)
        self.assertEqual(headers["apns-collapse-id"], "uuid-123")

    def test_ios_keeps_existing_priority_header(self):
        data = {"notification_type": "oneHour", "launch_uuid": "uuid-123"}
        self.mixin.send_notif_v5_ios(data=data, topics="'prod_v5_ios' in topics")
        headers = _ios_apns_headers(self.mixin.fcm)
        self.assertEqual(headers["apns-priority"], "10")


class EventCollapseIdTests(SimpleTestCase):
    def setUp(self):
        # Subclass of NotificationService whose __init__ needs FCM creds — bypass it.
        self.handler = EventNotificationHandler.__new__(EventNotificationHandler)
        self.handler.fcm = mock.MagicMock()
        self.handler.DEBUG = True

    def test_ios_sets_apns_collapse_id_with_event_prefix(self):
        v5 = {"notification_type": "event", "title": "t", "body": "b", "event_id": "999"}
        with mock.patch.object(self.handler, "_build_v5_event_data", return_value=v5):
            self.handler._send_v5_event_notification(event=object(), event_type="event")
        headers = _ios_apns_headers(self.handler.fcm)
        self.assertEqual(headers["apns-collapse-id"], "event_999")


class NewsCollapseIdTests(SimpleTestCase):
    def setUp(self):
        self.handler = NewsNotificationHandler.__new__(NewsNotificationHandler)
        self.handler.fcm = mock.MagicMock()
        self.handler.DEBUG = True

    def test_ios_sets_apns_collapse_id_with_news_prefix(self):
        v5 = {"notification_type": "featured_news", "title": "t", "body": "b", "article_id": "777"}
        with mock.patch.object(self.handler, "_build_v5_news_data", return_value=v5):
            self.handler._send_v5_notification(article=object())
        headers = _ios_apns_headers(self.handler.fcm)
        self.assertEqual(headers["apns-collapse-id"], "news_777")


class CustomCollapseIdTests(SimpleTestCase):
    def setUp(self):
        self.mixin = CustomNotificationMixin()
        self.mixin.fcm = mock.MagicMock()
        self.mixin.DEBUG = True

    def test_ios_sets_apns_collapse_id_with_custom_prefix(self):
        v5 = {"notification_type": "custom", "title": "t", "body": "b", "custom_id": "cust-1"}
        with mock.patch.object(self.mixin, "_build_v5_custom_data", return_value=v5):
            self.mixin._send_v5_custom_ios(pending=object())
        headers = _ios_apns_headers(self.mixin.fcm)
        self.assertEqual(headers["apns-collapse-id"], "custom_cust-1")
