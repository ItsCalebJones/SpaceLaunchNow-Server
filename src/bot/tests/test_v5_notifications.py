"""QA tests for the V5 news + custom notification path.

Test-only — no production code is changed. These exercise the V5 payload
builders directly and the two tracker dispatch methods (check_news_item /
check_custom) with the FCM sends, social posting, and ORM access mocked, so no
database or live FCM is required. They run under settings.test via the Django
test runner.
"""

from unittest import mock

from django.test import SimpleTestCase

from bot.app.events.event_tracker import EventTracker
from bot.app.notifications.custom import CustomNotificationMixin
from bot.app.notifications.launch_event_tracker import LaunchEventTracker
from bot.app.notifications.news_notification_handler import NewsNotificationHandler

NEWS_KEYS = {
    "notification_type",
    "title",
    "body",
    "article_id",
    "article_title",
    "article_news_site",
    "article_url",
    "article_image",
}

CUSTOM_KEYS = {
    "notification_type",
    "title",
    "body",
    "custom_id",
    "target_type",
    "target_id",
    "target_url",
    "custom_image",
}


def _attr(**kw):
    return type("Obj", (), kw)


# --------------------------------------------------------------------------- #
# 1. _build_v5_news_data
# --------------------------------------------------------------------------- #
class BuildV5NewsDataTests(SimpleTestCase):
    def setUp(self):
        # Builder is pure; bypass NotificationService.__init__ (which needs FCM creds).
        self.handler = NewsNotificationHandler.__new__(NewsNotificationHandler)

    def _article(self, featured_image="https://img.example/a.jpg"):
        return _attr(
            id=12345,
            news_site="SpaceNews",
            title="Falcon 9 launches batch of satellites",
            link="https://example.com/article",
            featured_image=featured_image,
        )

    def test_exact_eight_keys(self):
        data = self.handler._build_v5_news_data(self._article())
        self.assertEqual(set(data.keys()), NEWS_KEYS)

    def test_no_foreign_detection_keys(self):
        data = self.handler._build_v5_news_data(self._article())
        self.assertNotIn("event_id", data)
        self.assertNotIn("lsp_id", data)
        self.assertFalse([k for k in data if k.startswith("custom_")])

    def test_field_values(self):
        article = self._article()
        data = self.handler._build_v5_news_data(article)
        self.assertEqual(data["notification_type"], "featured_news")
        self.assertEqual(data["article_id"], "12345")
        self.assertEqual(data["article_url"], article.link)
        self.assertEqual(data["title"], "New article via SpaceNews")
        self.assertEqual(data["body"], article.title)
        self.assertEqual(data["article_news_site"], "SpaceNews")
        self.assertEqual(data["article_title"], article.title)

    def test_image_empty_string_fallback(self):
        data = self.handler._build_v5_news_data(self._article(featured_image=None))
        self.assertEqual(data["article_image"], "")

    def test_all_values_are_strings(self):
        data = self.handler._build_v5_news_data(self._article())
        self.assertTrue(all(isinstance(v, str) for v in data.values()))


# --------------------------------------------------------------------------- #
# 2. _build_v5_custom_data
# --------------------------------------------------------------------------- #
class BuildV5CustomDataTests(SimpleTestCase):
    def setUp(self):
        self.mixin = CustomNotificationMixin()

    def _pending(self, launch_id=None, news_id=None, event_id=None):
        return _attr(
            id="cust-1",
            title="Announcement",
            message="Body text",
            launch_id=launch_id,
            news_id=news_id,
            event_id=event_id,
        )

    def test_none_target(self):
        data = self.mixin._build_v5_custom_data(self._pending())
        self.assertEqual(set(data.keys()), CUSTOM_KEYS)
        self.assertEqual(data["notification_type"], "custom")
        self.assertEqual(data["target_type"], "none")
        self.assertEqual(data["target_id"], "")
        self.assertEqual(data["target_url"], "")
        self.assertEqual(data["custom_image"], "")
        self.assertEqual(data["custom_id"], "cust-1")

    def test_launch_target(self):
        launch = _attr(
            id="launch-uuid-abc",
            image=_attr(image=_attr(url="https://img.example/launch.png")),
            launch_service_provider=None,
        )
        with mock.patch("bot.app.notifications.custom.Launch") as Launch:
            Launch.objects.get.return_value = launch
            data = self.mixin._build_v5_custom_data(self._pending(launch_id="launch-uuid-abc"))
        self.assertEqual(set(data.keys()), CUSTOM_KEYS)
        self.assertEqual(data["notification_type"], "custom")
        self.assertEqual(data["target_type"], "launch")
        self.assertEqual(data["target_id"], "launch-uuid-abc")
        self.assertEqual(data["target_url"], "")
        self.assertEqual(data["custom_image"], "https://img.example/launch.png")
        self.assertNotIn("launch_id", data)

    def test_news_target(self):
        article = _attr(id=777, link="https://example.com/news", featured_image="https://img.example/n.jpg")
        with mock.patch("bot.app.notifications.custom.Article") as Article:
            Article.objects.get.return_value = article
            data = self.mixin._build_v5_custom_data(self._pending(news_id=777))
        self.assertEqual(set(data.keys()), CUSTOM_KEYS)
        self.assertEqual(data["notification_type"], "custom")
        self.assertEqual(data["target_type"], "news")
        self.assertEqual(data["target_id"], "777")
        self.assertEqual(data["target_url"], "https://example.com/news")
        self.assertEqual(data["custom_image"], "https://img.example/n.jpg")

    def test_event_target_is_typed_custom_with_no_top_level_event_id(self):
        """CRITICAL: an event-ref custom must NOT be mis-detected as an event."""
        event = _attr(id=999, image=_attr(image=_attr(url="https://img.example/event.png")))
        with mock.patch("bot.app.notifications.custom.Events") as Events:
            Events.objects.get.return_value = event
            data = self.mixin._build_v5_custom_data(self._pending(event_id=999))
        self.assertEqual(set(data.keys()), CUSTOM_KEYS)
        self.assertEqual(data["notification_type"], "custom")  # (a)
        self.assertNotIn("event_id", data)  # (b) clean dict
        self.assertEqual(data["target_type"], "event")
        self.assertEqual(data["target_id"], "999")
        self.assertEqual(data["target_url"], "")
        self.assertEqual(data["custom_image"], "https://img.example/event.png")

    def test_all_values_are_strings(self):
        data = self.mixin._build_v5_custom_data(self._pending())
        self.assertTrue(all(isinstance(v, str) for v in data.values()))


# --------------------------------------------------------------------------- #
# 3. check_news_item dispatch wiring
# --------------------------------------------------------------------------- #
class CheckNewsItemTests(SimpleTestCase):
    def _build_tracker(self):
        # Avoid constructing real handlers (FCM creds) inside EventTracker.__init__.
        with mock.patch("bot.app.events.event_tracker.EventNotificationHandler"), mock.patch(
            "bot.app.events.event_tracker.NewsNotificationHandler"
        ):
            tracker = EventTracker(debug=True)
        tracker.news_notification_handler = mock.MagicMock()
        return tracker

    def test_send_to_social_and_v5_send_both_called_when_allowed(self):
        tracker = self._build_tracker()
        record = _attr(id=42, was_notified=False, sent_at=None, should_notify=True, save=mock.MagicMock())
        article = _attr(id=42, title="An article")

        with mock.patch("bot.app.events.event_tracker.ArticleNotification") as AN, mock.patch(
            "bot.app.events.event_tracker.Article"
        ) as Article, mock.patch.object(
            EventTracker, "check_if_news_notification_allowed", new_callable=mock.PropertyMock
        ) as allowed:
            AN.objects.filter.return_value = [record]
            Article.objects.get.return_value = article
            allowed.return_value = True

            tracker.check_news_item()

        tracker.news_notification_handler.send_to_social.assert_called_once_with(article)
        tracker.news_notification_handler.send_notification.assert_called_once_with(article)
        self.assertTrue(record.was_notified)

    def test_nothing_sent_when_not_allowed(self):
        tracker = self._build_tracker()
        record = _attr(id=42, was_notified=False, sent_at=None, should_notify=True, save=mock.MagicMock())
        article = _attr(id=42, title="An article")

        with mock.patch("bot.app.events.event_tracker.ArticleNotification") as AN, mock.patch(
            "bot.app.events.event_tracker.Article"
        ) as Article, mock.patch.object(
            EventTracker, "check_if_news_notification_allowed", new_callable=mock.PropertyMock
        ) as allowed:
            AN.objects.filter.return_value = [record]
            Article.objects.get.return_value = article
            allowed.return_value = False

            tracker.check_news_item()

        tracker.news_notification_handler.send_to_social.assert_not_called()
        tracker.news_notification_handler.send_notification.assert_not_called()


# --------------------------------------------------------------------------- #
# 4. check_custom dispatch wiring
# --------------------------------------------------------------------------- #
class CheckCustomTests(SimpleTestCase):
    def _build_tracker(self):
        with mock.patch("bot.app.notifications.launch_event_tracker.NotificationHandler"), mock.patch(
            "bot.app.notifications.launch_event_tracker.NetstampHandler"
        ):
            tracker = LaunchEventTracker(debug=True)
        tracker.notification_handler = mock.MagicMock()
        return tracker

    def _pending(self, **kw):
        defaults = dict(send_ios_complete=False, send_android_complete=False, save=mock.MagicMock())
        defaults.update(kw)
        return _attr(**defaults)

    def _run(self, tracker, pending_ios, pending_android):
        with mock.patch("bot.app.notifications.launch_event_tracker.Notification") as N:
            # filter() is called twice: first for ios, then android.
            N.objects.filter.side_effect = [pending_ios, pending_android]
            tracker.check_custom()

    def test_ios_only_dispatches_ios_and_marks_ios_complete(self):
        tracker = self._build_tracker()
        p = self._pending()
        self._run(tracker, [p], [])
        tracker.notification_handler._send_v5_custom_ios.assert_called_once_with(p)
        tracker.notification_handler._send_v5_custom_android.assert_not_called()
        self.assertTrue(p.send_ios_complete)
        self.assertFalse(p.send_android_complete)

    def test_android_only_dispatches_android_and_marks_android_complete(self):
        tracker = self._build_tracker()
        p = self._pending()
        self._run(tracker, [], [p])
        tracker.notification_handler._send_v5_custom_android.assert_called_once_with(p)
        tracker.notification_handler._send_v5_custom_ios.assert_not_called()
        self.assertTrue(p.send_android_complete)
        self.assertFalse(p.send_ios_complete)

    def test_both_platforms_sent_once_per_platform_not_doubled(self):
        tracker = self._build_tracker()
        # A record flagged for both appears in BOTH querysets (matching real ORM behavior).
        p = self._pending()
        self._run(tracker, [p], [p])
        # Exactly one ios send and one android send — never doubled to the same platform.
        tracker.notification_handler._send_v5_custom_ios.assert_called_once_with(p)
        tracker.notification_handler._send_v5_custom_android.assert_called_once_with(p)
        self.assertTrue(p.send_ios_complete)
        self.assertTrue(p.send_android_complete)

    def test_complete_flipped_after_send(self):
        """The send happens before the _complete flag is set + saved."""
        tracker = self._build_tracker()
        order = []
        p = self._pending(save=mock.MagicMock(side_effect=lambda: order.append("save")))
        tracker.notification_handler._send_v5_custom_ios.side_effect = lambda pending: order.append("send")
        self._run(tracker, [p], [])
        self.assertEqual(order, ["send", "save"])

    def test_send_failure_leaves_complete_false_for_requeue(self):
        """A send raising must leave _complete False so the record is re-queued."""
        tracker = self._build_tracker()
        p = self._pending()
        tracker.notification_handler._send_v5_custom_ios.side_effect = RuntimeError("FCM down")
        with mock.patch("bot.app.notifications.launch_event_tracker.Notification") as N:
            N.objects.filter.side_effect = [[p], []]
            with self.assertRaises(RuntimeError):
                tracker.check_custom()
        # Mark-after-send means the flag was never set and save() never ran for this record.
        self.assertFalse(p.send_ios_complete)
        p.save.assert_not_called()
