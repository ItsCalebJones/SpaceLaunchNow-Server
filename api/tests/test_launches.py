import json
from rest_framework import status
from rest_framework.test import APITestCase

from bot.app.repository.launches_repository import LaunchRepository


class LaunchTests(APITestCase):
    def setUp(self):
        self.repository = LaunchTests.repository
        self.launches = LaunchTests.launches

    @classmethod
    def setUpClass(cls):
        """ get_some_resource() is slow, to avoid calling it for each test use setUpClass()
            and store the result as class variable
        """
        super(LaunchTests, cls).setUpClass()
        cls.repository = LaunchRepository()
        cls.repository.get_launch_status()
        cls.repository.get_mission_type()
        cls.repository.get_agency_type()
        cls.repository.get_launch_by_id(864)
        cls.repository.get_launch_by_id(998)
        cls.launches = cls.repository.get_next_launches(2)

    def test_v300_upcoming_normal(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test Normal endpoint
        response = self.client.get('/3.0.0/launch/upcoming/?limit=1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['results'][0]['id'], self.launches[0].id)
        self.assertIsNotNone(data['results'][0]['isonet'])
        self.assertIsNotNone(data['results'][0]['netstamp'])

    def test_v300_upcoming_list(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test list endpoint
        response = self.client.get('/3.0.0/launch/upcoming/?limit=1&mode=list')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['results'][0]['id'], self.launches[0].id)
        self.assertNotIn('isonet', data['results'][0])
        self.assertNotIn('netstamp', data['results'][0])

    def test_v300_upcoming_detailed(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test detailed endpoint
        response = self.client.get('/3.0.0/launch/upcoming/?limit=1&mode=detailed')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['results'][0]['id'], self.launches[0].id)
        self.assertIn('founding_year', data['results'][0]['lsp'])

    def test_v300_previous_normal(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test Normal endpoint
        response = self.client.get('/3.0.0/launch/previous/?limit=1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['count'], 2)
        self.assertIsNotNone(data['results'][0]['isonet'])
        self.assertIsNotNone(data['results'][0]['netstamp'])

    def test_v300_previous_list(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test list endpoint
        response = self.client.get('/3.0.0/launch/previous/?limit=1&mode=list')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['count'], 2)
        self.assertNotIn('isonet', data['results'][0])
        self.assertNotIn('netstamp', data['results'][0])

    def test_v300_previous_detailed(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test detailed endpoint
        response = self.client.get('/3.0.0/launch/previous/?limit=1&mode=detailed')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['count'], 2)
        self.assertIn('founding_year', data['results'][0]['lsp'])

    def test_v310_upcoming_normal(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test Normal endpoint
        response = self.client.get('/3.1.0/launch/upcoming/?limit=1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['results'][0]['id'], self.launches[0].id)
        self.assertNotIn('netstamp', data['results'][0])
        self.assertNotIn('isonet', data['results'][0])
        self.assertIn('name', data['results'][0]['status'])

    def test_v310_upcoming_list(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test list endpoint
        response = self.client.get('/3.1.0/launch/upcoming/?limit=1&mode=list')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['results'][0]['id'], self.launches[0].id)
        self.assertNotIn('netstamp', data['results'][0])
        self.assertNotIn('isonet', data['results'][0])
        self.assertIn('name', data['results'][0]['status'])

    def test_v310_upcoming_detailed(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test detailed endpoint
        response = self.client.get('/3.1.0/launch/upcoming/?limit=1&mode=detailed')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['results'][0]['id'], self.launches[0].id)
        self.assertNotIn('netstamp', data['results'][0])
        self.assertNotIn('isonet', data['results'][0])
        self.assertIn('founding_year', data['results'][0]['lsp'])
        self.assertIn('name', data['results'][0]['status'])

    def test_v310_previous_normal(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test Normal endpoint
        response = self.client.get('/3.1.0/launch/previous/?limit=1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['count'], 2)
        self.assertNotIn('netstamp', data['results'][0])
        self.assertNotIn('isonet', data['results'][0])
        self.assertIn('name', data['results'][0]['status'])

    def test_v310_previous_list(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test list endpoint
        response = self.client.get('/3.1.0/launch/previous/?limit=1&mode=list')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['count'], 2)
        self.assertNotIn('netstamp', data['results'][0])
        self.assertNotIn('isonet', data['results'][0])
        self.assertIn('name', data['results'][0]['status'])

    def test_v310_previous_detailed(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test detailed endpoint
        response = self.client.get('/3.1.0/launch/previous/?limit=1&mode=detailed')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['count'], 2)
        self.assertNotIn('netstamp', data['results'][0])
        self.assertNotIn('isonet', data['results'][0])
        self.assertIn('founding_year', data['results'][0]['lsp'])
        self.assertIn('name', data['results'][0]['status'])

    def test_v320_upcoming_normal(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test Normal endpoint
        response = self.client.get('/3.2.0/launch/upcoming/?limit=1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['results'][0]['id'], self.launches[0].id)
        self.assertNotIn('netstamp', data['results'][0])
        self.assertNotIn('isonet', data['results'][0])
        self.assertIn('name', data['results'][0]['status'])
        self.assertIn('rocket', data['results'][0])
        self.assertIn('net', data['results'][0])
        self.assertIn('configuration', data['results'][0]['rocket'])
        self.assertIn('first_stage', data['results'][0]['rocket'])
        self.assertIn('pad', data['results'][0])
        self.assertIn('location', data['results'][0]['pad'])

    def test_v320_upcoming_list(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test list endpoint
        response = self.client.get('/3.2.0/launch/upcoming/?limit=1&mode=list')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['results'][0]['id'], self.launches[0].id)
        self.assertNotIn('netstamp', data['results'][0])
        self.assertNotIn('isonet', data['results'][0])
        self.assertNotIn('rocket', data['results'][0])
        self.assertIn('name', data['results'][0]['status'])
        self.assertIn('name', data['results'][0])
        self.assertIn('net', data['results'][0])
        self.assertIn('pad', data['results'][0])
        self.assertIn('landing', data['results'][0])
        self.assertIn('orbit', data['results'][0])

    def test_v320_upcoming_detailed(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test detailed endpoint
        response = self.client.get('/3.2.0/launch/upcoming/?limit=1&mode=detailed')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['results'][0]['id'], self.launches[0].id)
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

    def test_v320_previous_normal(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test Normal endpoint
        response = self.client.get('/3.2.0/launch/previous/?limit=1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['count'], 2)
        self.assertNotIn('netstamp', data['results'][0])
        self.assertNotIn('isonet', data['results'][0])
        self.assertIn('name', data['results'][0]['status'])
        self.assertIn('rocket', data['results'][0])
        self.assertIn('net', data['results'][0])
        self.assertIn('configuration', data['results'][0]['rocket'])
        self.assertIn('first_stage', data['results'][0]['rocket'])
        self.assertIn('pad', data['results'][0])
        self.assertIn('location', data['results'][0]['pad'])

    def test_v320_previous_list(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test list endpoint
        response = self.client.get('/3.2.0/launch/previous/?limit=1&mode=list')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['count'], 2)
        self.assertNotIn('netstamp', data['results'][0])
        self.assertNotIn('isonet', data['results'][0])
        self.assertNotIn('rocket', data['results'][0])
        self.assertIn('name', data['results'][0]['status'])
        self.assertIn('name', data['results'][0])
        self.assertIn('net', data['results'][0])
        self.assertIn('pad', data['results'][0])
        self.assertIn('landing', data['results'][0])
        self.assertIn('orbit', data['results'][0])

    def test_v320_previous_detailed(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test detailed endpoint
        response = self.client.get('/3.2.0/launch/previous/?limit=1&mode=detailed')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['count'], 2)
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
