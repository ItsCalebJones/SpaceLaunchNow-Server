import json
import pathlib

from api.models import Launch
from api.tests.test__base import LLAPITests
from django.template.loader import render_to_string

# Create your tests here.
from rest_framework import status


class WebTests(LLAPITests):
    def test_home(self):
        # Test Normal endpoint
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_next(self):
        # Test Normal endpoint
        response = self.client.get("/next/")
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_launches(self):
        # Test Normal endpoint
        response = self.client.get("/launch/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_launch_by_id(self):
        # Test Normal endpoint
        launch = Launch.objects.first()
        response = self.client.get(f"/launch/{launch.id}")
        self.assertEqual(response.status_code, status.HTTP_301_MOVED_PERMANENTLY)

    def test_upcoming_launches_label_their_timezone(self):
        """Regression: times were rendered unlabeled, in a timezone that silently
        alternated between UTC and viewer-local depending on session state."""
        response = self.client.get("/launch/upcoming/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        html = response.content.decode()
        self.assertIn('class="sln-time"', html)
        # Every rendered time must be anchored to an explicit UTC instant.
        self.assertIn("+00:00", html)

    def test_mobile_launch_detail_renders_a_date(self):
        """Regression: the mobile detail page left #date empty and the only code
        that filled it was commented out, so no launch date rendered at all."""
        launch = Launch.objects.first()
        response = self.client.get(
            f"/launch/{launch.slug}/",
            HTTP_USER_AGENT=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
                "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
            ),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        html = response.content.decode()
        self.assertIn('id="date"', html)
        self.assertIn('class="sln-time"', html)

    def test_pages_using_the_video_facade_still_render(self):
        """Smoke cover for the three templates whose {% video %} blocks were replaced
        by the facade include. Without this, a broken tag there fails silently."""
        for path_ in ("/starship/", "/event/", "/app"):
            with self.subTest(path=path_):
                self.assertEqual(
                    self.client.get(path_).status_code, status.HTTP_200_OK
                )

    def test_no_user_agent_branching_in_templates(self):
        """Any surviving is_mobile branch makes the HTML User-Agent dependent. The
        nginx cache key has no User-Agent, so such a page is served to the wrong
        device -- which is how the mobile <h1> went missing from Google's index."""
        root = pathlib.Path(__file__).resolve().parent / "templates" / "web"
        offenders = sorted(
            str(path.relative_to(root))
            for path in root.rglob("*.html")
            if "is_mobile" in path.read_text(encoding="utf-8", errors="replace")
        )
        self.assertEqual(offenders, [])

    def test_video_facade_defers_the_iframe(self):
        """The facade must ship a thumbnail and no iframe. A hidden or unwatched
        iframe still downloads the whole YouTube embed."""
        html = render_to_string(
            "web/partials/video_embed.html",
            {"video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "title": "Watch Live"},
        )
        self.assertIn("sln-video-facade", html)
        self.assertIn('data-video-code="dQw4w9WgXcQ"', html)
        self.assertIn('aria-label="Play Watch Live"', html)
        self.assertNotIn("<iframe", html)
        self.assertNotIn("youtube.com/embed", html)

    def test_video_facade_renders_nothing_without_a_url(self):
        """Callers previously guarded with {% if %}; the partial keeps that contract."""
        html = render_to_string("web/partials/video_embed.html", {"video_url": None})
        self.assertEqual(html.strip(), "")

    def test_smart_app_banner_present(self):
        """iOS Safari renders this natively and every other browser ignores it, so it
        ships to everyone unconditionally -- making it UA-conditional would put the
        page back in the uncacheable state this work exists to fix."""
        html = self.client.get("/").content.decode()
        self.assertIn('name="apple-itunes-app"', html)
        self.assertIn("app-id=1399715731", html)

    def test_apple_app_site_association(self):
        """Universal Links require this served as JSON, at this exact path, with no
        redirect and no file extension. Inert until the iOS app ships the
        associated-domains entitlement, but the contract still has to be right."""
        response = self.client.get("/.well-known/apple-app-site-association")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/json")
        details = json.loads(response.content.decode())["applinks"]["details"]
        self.assertEqual(details[0]["appIDs"], ["4T4QRN2U5X.me.spacelaunchnow.spacelaunchnow"])
        self.assertIn("/launch/*", [component["/"] for component in details[0]["components"]])
