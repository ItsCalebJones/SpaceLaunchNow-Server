"""Tests for LaunchEventTracker.check_next_stamp_changed (Tasks#438).

A record whose last_net_stamp is None must be seeded from launch.net, so a later
NET slip of more than two hours resets the countdown flags. ORM and sends are mocked.
"""

from datetime import datetime, timedelta
from unittest import mock

import pytz
from django.test import SimpleTestCase

from bot.app.notifications.launch_event_tracker import LaunchEventTracker

FLAGS = [
    "wasNotifiedTwentyFourHour",
    "wasNotifiedOneHour",
    "wasNotifiedTenMinutes",
    "wasNotifiedOneMinute",
    "wasNotifiedWebcastLive",
]


class FakeRecord:
    def __init__(self, last_net_stamp=None, flags_set=True):
        self.last_net_stamp = last_net_stamp
        self.last_net_stamp_timestamp = None
        for flag in FLAGS:
            setattr(self, flag, flags_set)
        self.save = mock.MagicMock()


class CheckNextStampChangedTests(SimpleTestCase):
    def _tracker(self):
        with (
            mock.patch("bot.app.notifications.launch_event_tracker.NotificationHandler"),
            mock.patch("bot.app.notifications.launch_event_tracker.NetstampHandler"),
            mock.patch("bot.app.notifications.netstamp_handler.NotificationHandler"),
        ):
            tracker = LaunchEventTracker(debug=True)
        # Real handler logic with the send mocked, so flag resets are exercised.
        from bot.app.notifications.netstamp_handler import NetstampHandler

        with mock.patch("bot.app.notifications.netstamp_handler.NotificationHandler"):
            tracker.netstamp = NetstampHandler()
        return tracker

    def _launch(self, net):
        return mock.MagicMock(id="abc", net=net, **{"name": "Test launch"})

    def _check(self, tracker, launch, record):
        with mock.patch("bot.app.notifications.launch_event_tracker.LaunchNotificationRecord") as R:
            R.objects.get_or_create.return_value = (record, False)
            tracker.check_next_stamp_changed(launch)

    def test_none_stamp_is_seeded_on_first_check(self):
        net = datetime.now(tz=pytz.utc) + timedelta(hours=20)
        record = FakeRecord(last_net_stamp=None)
        self._check(self._tracker(), self._launch(net), record)
        self.assertEqual(record.last_net_stamp, net)
        self.assertIsNotNone(record.last_net_stamp_timestamp)
        record.save.assert_called_once()
        for flag in FLAGS:
            self.assertTrue(getattr(record, flag), flag)

    def test_slip_over_two_hours_resets_countdown_flags(self):
        old_net = datetime.now(tz=pytz.utc) + timedelta(hours=20)
        new_net = old_net + timedelta(days=2)
        record = FakeRecord(last_net_stamp=old_net)
        self._check(self._tracker(), self._launch(new_net), record)
        for flag in FLAGS:
            self.assertFalse(getattr(record, flag), flag)
        self.assertEqual(record.last_net_stamp, new_net)

    def test_seed_then_slip_resets_flags(self):
        old_net = datetime.now(tz=pytz.utc) + timedelta(hours=20)
        record = FakeRecord(last_net_stamp=None)
        tracker = self._tracker()
        self._check(tracker, self._launch(old_net), record)
        self._check(tracker, self._launch(old_net + timedelta(days=3)), record)
        for flag in FLAGS:
            self.assertFalse(getattr(record, flag), flag)

    def test_slip_under_two_hours_keeps_flags(self):
        old_net = datetime.now(tz=pytz.utc) + timedelta(hours=20)
        record = FakeRecord(last_net_stamp=old_net)
        self._check(self._tracker(), self._launch(old_net + timedelta(minutes=90)), record)
        for flag in FLAGS:
            self.assertTrue(getattr(record, flag), flag)
        self.assertEqual(record.last_net_stamp, old_net)
        record.save.assert_not_called()
