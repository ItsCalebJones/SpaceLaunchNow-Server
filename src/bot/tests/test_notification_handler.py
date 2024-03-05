import logging
from unittest.mock import patch

from api.models import Article, Events, InfoURLs, Launch, LaunchStatus, VidURLs
from api.tests.test__base import LLAPITests
from django.core.cache import cache

from bot.app.notifications.notification_handler import NotificationHandler
from bot.models import LaunchNotificationRecord, Notification

logger = logging.getLogger(__name__)


class NotificationHandlerTestCase(LLAPITests):
    def setUp(self):
        self.handler = NotificationHandler()

    def tearDown(self):
        cache.clear()

    def test_send_notification(self):
        launch = Launch.objects.all().first()
        launch.status = LaunchStatus.objects.get(id=1)
        notification_type = "netstampChanged"
        notification, create = LaunchNotificationRecord.objects.get_or_create(launch_id=launch.id)

        with patch("bot.app.notifications.notification_handler.FCMNotification") as mock_push_service:
            self.handler.send_notification(launch, notification_type, notification)

            # Assert that the notification is saved
            notification.refresh_from_db()
            self.assertIsNotNone(notification.last_notification_sent)

            # Assert that the FCMNotification.notify_topic_subscribers method is called
            assert mock_push_service.return_value.notify_topic_subscribers.call_count == 4
        notification.delete()

    def test_send_notification_with_cooldown(self):
        launch = Launch.objects.all().first()
        notification_type = "netstampChanged"
        notification, create = LaunchNotificationRecord.objects.get_or_create(launch_id=launch.id)

        # Set a cooldown for the launch and global notification types
        cache.set(
            str(launch.id) + notification_type,
            "ID: %s Net: %s Type: %s" % (launch.id, launch.net, notification_type),
            60,
        )
        cache.set(notification_type, "ID: %s Net: %s Type: %s" % (launch.id, launch.net, notification_type), 60)

        with patch("bot.app.notifications.notification_handler.FCMNotification") as mock_push_service:
            self.handler.send_notification(launch, notification_type, notification)

            # Assert that the notification is not saved
            notification.refresh_from_db()
            self.assertIsNone(notification.last_notification_sent)

            # Assert that the FCMNotification.notify_topic_subscribers method is not called
            mock_push_service.return_value.notify_topic_subscribers.assert_not_called()
        notification.delete()

    def test_send_notification_with_invalid_state(self):
        launch = Launch.objects.all().first()
        notification_type = "netstampChanged"
        notification, create = LaunchNotificationRecord.objects.get_or_create(launch_id=launch.id)

        # Set an invalid state for the launch
        launch.status.id = 3
        launch.save()

        with patch("bot.app.notifications.notification_handler.FCMNotification") as mock_push_service:
            self.handler.send_notification(launch, notification_type, notification)

            # Assert that the notification is not saved
            notification.refresh_from_db()
            self.assertIsNone(notification.last_notification_sent)

            # Assert that the FCMNotification.notify_topic_subscribers method is not called
            mock_push_service.return_value.notify_topic_subscribers.assert_not_called()
        notification.delete()

    def test_get_json_data(self):
        # Create a launch object
        launch = Launch.objects.all().first()

        # Create a news object
        news = Article.objects.create(
            id=2,
            news_site="Test News Site",
            title="Test News Title",
            link="https://example.com/news",
            featured_image="https://example.com/news_image.jpg",
        )

        # Create an event object
        event = Events.objects.all().first()

        event.info_urls.add(InfoURLs.objects.create(info_url="https://example.com/event_info"))
        event.vid_urls.add(VidURLs.objects.create(vid_url="https://example.com/vid_info"))
        event.vid_urls.add(VidURLs.objects.create(vid_url="https://example.com/vid_info2"))

        pending = Notification.objects.create(
            launch_id=launch.id, news_id=news.id, event_id=event.id, title="Test Title", message="Test Message"
        )

        expected_data = {
            "notification_type": "custom",
            "click_action": "FLUTTER_NOTIFICATION_CLICK",
            "title": "Test Title",
            "message": "Test Message",
            "launch": {
                "launch_id": launch.launch_library_id,
                "launch_uuid": str(launch.id),
                "launch_name": launch.name,
                "launch_image": launch.image.image.url,
                "launch_net": launch.net.strftime("%B %d, %Y %H:%M:%S %Z"),
                "launch_location": launch.pad.location.name,
                "webcast": launch.webcast_live,
            },
            "news": {
                "id": news.id,
                "news_site_long": news.news_site,
                "title": news.title,
                "url": news.link,
                "featured_image": news.featured_image,
            },
            "event": {
                "id": event.id,
                "name": event.name,
                "description": event.description,
                "type": {
                    "id": event.type.id,
                    "name": event.type.name,
                },
                "date": event.date.strftime("%B %d, %Y %H:%M:%S %Z"),
                "location": event.location,
                "news_url": event.info_urls.first(),
                "video_url": event.vid_urls.first(),
                "webcast_live": event.webcast_live,
                "feature_image": event.image.image.url,
            },
        }

        result = self.handler.get_json_data(pending)
        self.assertEqual(result, expected_data)
