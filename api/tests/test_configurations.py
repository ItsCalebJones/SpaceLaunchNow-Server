import json

from rest_framework import status
from api.tests.test__base import SLNAPITests, LauncherConfig


class ConfigurationTests(SLNAPITests):

    def test_v1_configurations(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test Normal endpoint
        path = '/v1/launcher_details/'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['count'], LauncherConfig.objects.all().count())
        configuration = LauncherConfig.objects.get(launch_library_id=data['results'][0]['id'])
        self.assertEqual(data['results'][0]['id'], configuration.launch_library_id)
        self.assertEqual(data['results'][0]['full_name'], configuration.full_name)
        self.assertEqual(data['results'][0]['launch_mass'], configuration.launch_mass)
        self.assertEqual(data['results'][0]['agency'], configuration.launch_agency.name)

        self.check_permissions(path)

    def test_v200_configurations(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test Normal endpoint
        path = '/2.0.0/launchers/'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['count'], LauncherConfig.objects.all().count())
        configuration = LauncherConfig.objects.get(launch_library_id=data['results'][0]['id'])
        self.assertEqual(data['results'][0]['id'], configuration.launch_library_id)
        self.assertEqual(data['results'][0]['full_name'], configuration.full_name)
        self.assertEqual(data['results'][0]['launch_mass'], configuration.launch_mass)
        self.assertEqual(data['results'][0]['agency'], configuration.launch_agency.name)

        self.check_permissions(path)

    def test_v300_configurations(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test Normal endpoint
        path = '/3.0.0/launchers/'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['count'], LauncherConfig.objects.all().count())
        configuration = LauncherConfig.objects.get(launch_library_id=data['results'][0]['id'])
        self.assertEqual(data['results'][0]['id'], configuration.launch_library_id)
        self.assertEqual(data['results'][0]['full_name'], configuration.full_name)
        self.assertEqual(data['results'][0]['launch_mass'], configuration.launch_mass)
        self.assertEqual(data['results'][0]['agency']['name'], configuration.launch_agency.name)

        self.check_permissions(path)

    def test_v320_configurations(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test Normal endpoint
        path = '/3.2.0/launcher_config/'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['count'], LauncherConfig.objects.all().count())
        configuration = LauncherConfig.objects.get(launch_library_id=data['results'][0]['id'])
        self.assertEqual(data['results'][0]['id'], configuration.launch_library_id)
        self.assertEqual(data['results'][0]['full_name'], configuration.full_name)
        self.assertEqual(data['results'][0]['launch_mass'], configuration.launch_mass)
        self.assertEqual(data['results'][0]['launch_service_provider']['name'], configuration.launch_agency.name)

        self.check_permissions(path)
