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
