
import json
from rest_framework import status

from api.models import Launch
from api.tests.test__base import SLNAPITests


class LaunchTests(SLNAPITests):

    def test_v300_upcoming_normal(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test Normal endpoint
        path = '/3.0.0/launch/upcoming/?limit=1'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['count'], 2)
        launch = Launch.objects.get(launch_library_id=data['results'][0]['id'])
        self.assertEqual(data['results'][0]['id'], launch.launch_library_id)
        self.assertEqual(data['results'][0]['name'], launch.name)
        self.assertIsNotNone(data['results'][0]['isonet'])
        self.assertIsNotNone(data['results'][0]['netstamp'])

        self.check_permissions(path)

    def test_v300_upcoming_list(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test list endpoint
        path = '/3.0.0/launch/upcoming/?limit=1&mode=list'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['count'], 2)
        launch = Launch.objects.get(launch_library_id=data['results'][0]['id'])
        self.assertEqual(data['results'][0]['id'], launch.launch_library_id)
        self.assertEqual(data['results'][0]['name'], launch.name)
        self.assertNotIn('isonet', data['results'][0])
        self.assertNotIn('netstamp', data['results'][0])

        self.check_permissions(path)

    def test_v300_upcoming_detailed(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test detailed endpoint
        path = '/3.0.0/launch/upcoming/?limit=1&mode=detailed'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['count'], 2)
        launch = Launch.objects.get(launch_library_id=data['results'][0]['id'])
        self.assertEqual(data['results'][0]['id'], launch.launch_library_id)
        self.assertEqual(data['results'][0]['name'], launch.name)
        if data['results'][0]['lsp']:
            self.assertIn('founding_year', data['results'][0]['lsp'])

        self.check_permissions(path)

    def test_v300_previous_normal(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test Normal endpoint
        path = '/3.0.0/launch/previous/?limit=1'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['count'], 2)
        self.assertIsNotNone(data['results'][0]['isonet'])
        self.assertIsNotNone(data['results'][0]['netstamp'])

        self.check_permissions(path)

    def test_v300_previous_list(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test list endpoint
        path = '/3.0.0/launch/previous/?limit=1&mode=list'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['count'], 2)
        self.assertNotIn('isonet', data['results'][0])
        self.assertNotIn('netstamp', data['results'][0])

        self.check_permissions(path)

    def test_v300_previous_detailed(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test detailed endpoint
        path = '/3.0.0/launch/previous/?limit=1&mode=detailed'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['count'], 2)
        self.assertIn('founding_year', data['results'][0]['lsp'])

        self.check_permissions(path)

    def test_v310_upcoming_normal(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test Normal endpoint
        path = '/3.1.0/launch/upcoming/?limit=1'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['count'], 2)
        launch = Launch.objects.get(launch_library_id=data['results'][0]['id'])
        self.assertEqual(data['results'][0]['id'], launch.launch_library_id)
        self.assertEqual(data['results'][0]['name'], launch.name)
        self.assertNotIn('netstamp', data['results'][0])
        self.assertNotIn('isonet', data['results'][0])
        self.assertIn('name', data['results'][0]['status'])

        self.check_permissions(path)

    def test_v310_upcoming_list(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test list endpoint
        path = '/3.1.0/launch/upcoming/?limit=1&mode=list'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['count'], 2)
        launch = Launch.objects.get(launch_library_id=data['results'][0]['id'])
        self.assertEqual(data['results'][0]['id'], launch.launch_library_id)
        self.assertEqual(data['results'][0]['name'], launch.name)
        self.assertNotIn('netstamp', data['results'][0])
        self.assertNotIn('isonet', data['results'][0])
        self.assertIn('name', data['results'][0]['status'])

        self.check_permissions(path)

    def test_v310_upcoming_detailed(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test detailed endpoint
        path = '/3.1.0/launch/upcoming/?limit=1&mode=detailed'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['count'], 2)
        launch = Launch.objects.get(launch_library_id=data['results'][0]['id'])
        self.assertEqual(data['results'][0]['id'], launch.launch_library_id)
        self.assertEqual(data['results'][0]['name'], launch.name)
        self.assertNotIn('netstamp', data['results'][0])
        self.assertNotIn('isonet', data['results'][0])
        self.assertIn('name', data['results'][0]['status'])
        if data['results'][0]['lsp']:
            self.assertIn('founding_year', data['results'][0]['lsp'])

        self.check_permissions(path)

    def test_v310_previous_normal(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test Normal endpoint
        path = '/3.1.0/launch/previous/?limit=1'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['count'], 2)
        launch = Launch.objects.get(launch_library_id=data['results'][0]['id'])
        self.assertEqual(data['results'][0]['id'], launch.launch_library_id)
        self.assertEqual(data['results'][0]['name'], launch.name)
        self.assertNotIn('netstamp', data['results'][0])
        self.assertNotIn('isonet', data['results'][0])
        self.assertIn('name', data['results'][0]['status'])

        self.check_permissions(path)

    def test_v310_previous_list(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test list endpoint
        path = '/3.1.0/launch/previous/?limit=1&mode=list'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['count'], 2)
        launch = Launch.objects.get(launch_library_id=data['results'][0]['id'])
        self.assertEqual(data['results'][0]['id'], launch.launch_library_id)
        self.assertEqual(data['results'][0]['name'], launch.name)
        self.assertNotIn('netstamp', data['results'][0])
        self.assertNotIn('isonet', data['results'][0])
        self.assertIn('name', data['results'][0]['status'])

        self.check_permissions(path)

    def test_v310_previous_detailed(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test detailed endpoint
        path = '/3.1.0/launch/previous/?limit=1&mode=detailed'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['count'], 2)
        launch = Launch.objects.get(launch_library_id=data['results'][0]['id'])
        self.assertEqual(data['results'][0]['id'], launch.launch_library_id)
        self.assertEqual(data['results'][0]['name'], launch.name)
        self.assertNotIn('netstamp', data['results'][0])
        self.assertNotIn('isonet', data['results'][0])
        self.assertIn('founding_year', data['results'][0]['lsp'])
        self.assertIn('name', data['results'][0]['status'])

        self.check_permissions(path)

    def test_v320_upcoming_normal(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test Normal endpoint
        path = '/3.2.0/launch/upcoming/?limit=1'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['count'], 2)
        launch = Launch.objects.get(launch_library_id=data['results'][0]['id'])
        self.assertEqual(data['results'][0]['id'], launch.launch_library_id)
        self.assertEqual(data['results'][0]['name'], launch.name)
        self.assertNotIn('netstamp', data['results'][0])
        self.assertNotIn('isonet', data['results'][0])
        self.assertIn('name', data['results'][0]['status'])
        self.assertIn('rocket', data['results'][0])
        self.assertIn('net', data['results'][0])
        self.assertIn('configuration', data['results'][0]['rocket'])
        self.assertIn('first_stage', data['results'][0]['rocket'])
        self.assertIn('pad', data['results'][0])
        self.assertIn('location', data['results'][0]['pad'])

        self.check_permissions(path)

    def test_v320_upcoming_list(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test list endpoint
        path = '/3.2.0/launch/upcoming/?limit=1&mode=list'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['count'], 2)
        launch = Launch.objects.get(launch_library_id=data['results'][0]['id'])
        self.assertEqual(data['results'][0]['id'], launch.launch_library_id)
        self.assertEqual(data['results'][0]['name'], launch.name)
        self.assertNotIn('netstamp', data['results'][0])
        self.assertNotIn('isonet', data['results'][0])
        self.assertNotIn('rocket', data['results'][0])
        self.assertIn('name', data['results'][0]['status'])
        self.assertIn('name', data['results'][0])
        self.assertIn('net', data['results'][0])
        self.assertIn('pad', data['results'][0])
        self.assertIn('landing', data['results'][0])
        self.assertIn('orbit', data['results'][0])

        self.check_permissions(path)

    def test_v320_upcoming_detailed(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test detailed endpoint
        path = '/3.2.0/launch/upcoming/?limit=1&mode=detailed'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['count'], 2)
        launch = Launch.objects.get(launch_library_id=data['results'][0]['id'])
        self.assertEqual(data['results'][0]['id'], launch.launch_library_id)
        self.assertEqual(data['results'][0]['name'], launch.name)
        self.assertNotIn('netstamp', data['results'][0])
        self.assertNotIn('isonet', data['results'][0])
        self.assertIn('name', data['results'][0]['status'])
        self.assertIn('rocket', data['results'][0])
        self.assertIn('net', data['results'][0])
        self.assertIn('configuration', data['results'][0]['rocket'])
        self.assertIn('diameter', data['results'][0]['rocket']['configuration'])
        self.assertIn('first_stage', data['results'][0]['rocket'])
        self.assertIn('pad', data['results'][0])
        self.assertIn('location', data['results'][0]['pad'])

        self.check_permissions(path)

    def test_v320_previous_normal(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test Normal endpoint
        path = '/3.2.0/launch/previous/?limit=1'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['count'], 2)
        launch = Launch.objects.get(launch_library_id=data['results'][0]['id'])
        self.assertEqual(data['results'][0]['id'], launch.launch_library_id)
        self.assertEqual(data['results'][0]['name'], launch.name)
        self.assertNotIn('netstamp', data['results'][0])
        self.assertNotIn('isonet', data['results'][0])
        self.assertIn('name', data['results'][0]['status'])
        self.assertIn('rocket', data['results'][0])
        self.assertIn('net', data['results'][0])
        self.assertIn('configuration', data['results'][0]['rocket'])
        self.assertIn('first_stage', data['results'][0]['rocket'])
        self.assertIn('pad', data['results'][0])
        self.assertIn('location', data['results'][0]['pad'])

        self.check_permissions(path)

    def test_v320_previous_list(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test list endpoint
        path = '/3.2.0/launch/previous/?limit=1&mode=list'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['count'], 2)
        launch = Launch.objects.get(launch_library_id=data['results'][0]['id'])
        self.assertEqual(data['results'][0]['id'], launch.launch_library_id)
        self.assertEqual(data['results'][0]['name'], launch.name)
        self.assertNotIn('netstamp', data['results'][0])
        self.assertNotIn('isonet', data['results'][0])
        self.assertNotIn('rocket', data['results'][0])
        self.assertIn('name', data['results'][0]['status'])
        self.assertIn('name', data['results'][0])
        self.assertIn('net', data['results'][0])
        self.assertIn('pad', data['results'][0])
        self.assertIn('landing', data['results'][0])
        self.assertIn('orbit', data['results'][0])

        self.check_permissions(path)

    def test_v320_previous_detailed(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test detailed endpoint
        path = '/3.2.0/launch/previous/?limit=1&mode=detailed'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['count'], 2)
        launch = Launch.objects.get(launch_library_id=data['results'][0]['id'])
        self.assertEqual(data['results'][0]['id'], launch.launch_library_id)
        self.assertEqual(data['results'][0]['name'], launch.name)
        self.assertNotIn('netstamp', data['results'][0])
        self.assertNotIn('isonet', data['results'][0])
        self.assertIn('name', data['results'][0]['status'])
        self.assertIn('rocket', data['results'][0])
        self.assertIn('net', data['results'][0])
        self.assertIn('configuration', data['results'][0]['rocket'])
        self.assertIn('diameter', data['results'][0]['rocket']['configuration'])
        self.assertIn('first_stage', data['results'][0]['rocket'])
        self.assertIn('pad', data['results'][0])
        self.assertIn('location', data['results'][0]['pad'])

        self.check_permissions(path)

    def test_v300_launch_with_landings(self):
        path = '/3.0.0/launch/864/'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertNotIn('next', data)
        self.assertNotIn('result', data)
        self.assertNotIn('previous', data)
        self.assertNotIn('count', data)
        launch = Launch.objects.get(launch_library_id=data['id'])
        self.assertEqual(data['id'], launch.launch_library_id)
        self.assertEqual(data['name'], launch.name)
        self.assertEqual(data['status'], launch.status.id)
        self.assertIn('netstamp', data)
        self.assertIn('wsstamp', data)
        self.assertIn('westamp', data)
        self.assertIn('net', data)
        self.assertIn('window_end', data)
        self.assertIn('window_start', data)
        self.assertIn('isonet', data)
        self.assertIn('isostart', data)
        self.assertIn('isoend', data)
        self.assertEqual(data['launcher']['id'], launch.rocket.configuration.id)
        self.assertEqual(data['mission']['id'], launch.mission.id)
        self.assertEqual(data['lsp']['id'], launch.rocket.configuration.launch_agency.id)
        self.assertEqual(data['location']['id'], launch.pad.location.id)
        self.assertEqual(data['pad']['id'], launch.pad.id)

    def test_v320_launch_with_landings(self):
        launch = Launch.objects.get(launch_library_id=864)
        # TODO add landing information.
        # launch.rocket.firststage.
        path = '/3.2.0/launch/864/'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertNotIn('next', data)
        self.assertNotIn('result', data)
        self.assertNotIn('previous', data)
        self.assertNotIn('count', data)
        self.assertEqual(data['id'], launch.launch_library_id)
        self.assertEqual(data['name'], launch.name)
        self.assertIn('slug', data)
        self.assertEqual(data['status']['id'], launch.status.id)
        self.assertNotIn('netstamp', data)
        self.assertNotIn('wsstamp', data)
        self.assertNotIn('westamp', data)
        self.assertIn('net', data)
        self.assertIn('window_end', data)
        self.assertIn('window_start', data)
        self.assertNotIn('isonet', data)
        self.assertNotIn('isostart', data)
        self.assertNotIn('isoend', data)
        self.assertEqual(data['rocket']['configuration']['id'], launch.rocket.configuration.id)
        self.assertEqual(data['rocket']['configuration']['launch_service_provider'], launch.rocket.configuration.launch_agency.name)
        self.assertEqual(len(data['rocket']['first_stage']), launch.rocket.firststage.count())
        for index, stage_data in enumerate(data['rocket']['first_stage']):
            stage = launch.rocket.firststage[index]
            self.assertEqual(stage_data['type'], stage.type.name)
            self.assertEqual(stage_data['reused'], stage.reused)
            self.assertEqual(stage_data['launcher_flight_number'], stage.launcher_flight_number)
            self.assertEqual(stage_data['launcher']['id'], stage.launcher.id)
            self.assertEqual(stage_data['launcher']['serial_number'], stage.launcher.serial_number)
            self.assertEqual(stage_data['landing']['attempt'], stage.landing.attempt)
            self.assertEqual(stage_data['landing']['success'], stage.landing.success)
            self.assertEqual(stage_data['landing']['description'], stage.landing.description)
            self.assertEqual(stage_data['landing']['location']['name'], stage.landing.location.name)
            self.assertEqual(stage_data['landing']['type']['name'], stage.landing.type.name)
        self.assertEqual(data['mission']['id'], launch.mission.id)
        self.assertEqual(data['pad']['id'], launch.pad.id)
        self.assertEqual(data['pad']['location']['id'], launch.pad.location.id)
