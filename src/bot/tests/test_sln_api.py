from api.models import Astronaut, Events, Launch, Launcher, LauncherConfig, SpacecraftConfiguration, SpaceStation
from api.tests.test__base import LLAPITests
from rest_framework import status


class SLNAPITest(LLAPITests):
    def test_ll_200_api_online(self):
        path = "/api/ll/2.0.0/"
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_ll_210_api_online(self):
        path = "/api/ll/2.1.0/"
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_ll_220_api_online(self):
        path = "/api/ll/2.2.0/"
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health_check(self):
        path = "/_health/"
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_launch_pages(self):
        path = "/next/"
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        path = "/launch/"
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        path = "/launch/upcoming/"
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        path = "/launch/previous/"
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_launch_slugs(self):
        launches = Launch.objects.all()
        for launch in launches:
            path = f"/launch/{launch.slug}/"
            response = self.client.get(path)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_event_slugs(self):
        events = Events.objects.all()
        for event in events:
            path = f"/event/{event.slug}/"
            response = self.client.get(path)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_vehicle(self):
        path = "/vehicle/"
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_launcher_links(self):
        path = "/vehicle/launcher"
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        launchers = Launcher.objects.all()
        for launcher in launchers:
            path = f"/vehicle/launcher/{launcher.id}/"
            response = self.client.get(path)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_launch_vehicle_links(self):
        path = "/vehicle/launch_vehicle"
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        launcher_configs = LauncherConfig.objects.all()
        for launcher_config in launcher_configs:
            path = f"/vehicle/launch_vehicle/{launcher_config.id}/"
            response = self.client.get(path)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_spacestation_links(self):
        path = "/vehicle/spacestation"
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        spacestations = SpaceStation.objects.all()
        for spacestation in spacestations:
            path = f"/vehicle/spacestation/{spacestation.id}/"
            response = self.client.get(path)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_spacecraft_links(self):
        path = "/vehicle/spacecraft"
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        spacecrafts = SpacecraftConfiguration.objects.all()
        for spacecraft in spacecrafts:
            path = f"/vehicle/spacecraft/{spacecraft.id}/"
            response = self.client.get(path)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_astronaut_links(self):
        path = "/astronaut/"
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        astronauts = Astronaut.objects.all()
        for astronaut in astronauts:
            path = f"/astronaut/{astronaut.id}/"
            response = self.client.get(path)
            self.assertEqual(response.status_code, status.HTTP_302_FOUND)

            path = f"/astronaut/{astronaut.slug}/"
            response = self.client.get(path)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_starship_dashboard(self):
        path = "/starship/"
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_about(self):
        path = "/about/"
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        path = "/about/staff/"
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        path = "/about/translators/"
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_site_meta(self):
        path = "/app/privacy"
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        path = "/app/privacy"
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        path = "/site/privacy"
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        path = "/site/privacy"
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        path = "/app-ads.txt"
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        path = "/ads.txt"
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        path = "/robots.txt"
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        path = "/sitemap.xml/"
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_ics(self):
        path = "/launches/latest/feed.ics"
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        path = "/events/latest/feed.ics"
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def check_permissions(self, path):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        response = self.client.post(path, **self.header)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.delete(path, **self.header)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.credentials()
        response = self.client.post(path)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.delete(path)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
