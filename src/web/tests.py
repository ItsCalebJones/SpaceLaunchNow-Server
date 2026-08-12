from api.models import Launch
from api.tests.test__base import LLAPITests

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
