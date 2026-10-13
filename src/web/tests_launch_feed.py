from datetime import timedelta

from api.models import Launch
from api.tests.test__base import LLAPITests
from django.test import override_settings
from django.utils import timezone
from icalendar import Calendar
from rest_framework import status

FEED_URL = "/launches/latest/feed.ics"


@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}})
class LaunchFeedTextEscapingTests(LLAPITests):
    """Tasks#113: a raw newline in launch text made the feed 500 with
    "Content line can not contain unescaped new line characters"."""

    def _seed(self, name="Falcon 9 Block 5 | Starlink\nGroup 1", description="Line one\nLine two\r\nLine three\rLine four"):
        launch = Launch.objects.order_by("id").first()
        Launch.objects.filter(pk=launch.pk).update(name=name, net=timezone.now() + timedelta(days=1))
        launch.refresh_from_db()
        mission = launch.mission
        mission.description = description
        mission.save()
        return launch

    def _content_lines(self, response):
        body = response.content.decode("utf-8")
        # RFC 5545: content lines end in CRLF; a bare CR or LF anywhere else is a defect.
        lines = body.split("\r\n")
        for line in lines:
            self.assertNotIn("\n", line)
            self.assertNotIn("\r", line)
        return lines

    def test_multiline_text_renders_escaped(self):
        launch = self._seed()
        response = self.client.get(FEED_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        lines = self._content_lines(response)
        unfolded = "\r\n".join(lines).replace("\r\n ", "")
        self.assertIn("SUMMARY:Falcon 9 Block 5 | Starlink\\nGroup 1", unfolded)
        self.assertIn("Line one\\nLine two\\nLine three\\nLine four", unfolded)
        self.assertIn(str(launch.id), unfolded)

    def test_special_characters_are_escaped_once(self):
        self._seed(name="A, B; C \\ D", description="x, y; z \\ w")
        response = self.client.get(FEED_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        unfolded = "\r\n".join(self._content_lines(response)).replace("\r\n ", "")
        self.assertIn("SUMMARY:A\\, B\\; C \\\\ D", unfolded)
        self.assertIn("x\\, y\\; z \\\\ w", unfolded)
        self.assertNotIn("\\\\,", unfolded)  # no double escaping

    def test_feed_with_multiline_launch_parses(self):
        self._seed()
        response = self.client.get(FEED_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        calendar = Calendar.from_ical(response.content)
        events = calendar.walk("VEVENT")
        self.assertTrue(events)
        summaries = [str(e.get("SUMMARY")) for e in events]
        self.assertIn("Falcon 9 Block 5 | Starlink\nGroup 1", summaries)

    def test_calendar_header_text_is_escaped(self):
        """The calendar-level X-WR-CALDESC is a static string with a newline; the library
        leaves unknown properties raw, which is what broke every request."""
        response = self.client.get(FEED_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        unfolded = "\r\n".join(self._content_lines(response)).replace("\r\n ", "")
        self.assertIn("X-WR-CALDESC:Rocket launch calendar feed generated for Space Launch Now.\\n", unfolded)

    def test_events_feed_renders(self):
        """Report only: /events/latest/feed.ics has no calendar-level description."""
        response = self.client.get("/events/latest/feed.ics")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
