import json
import unittest
from datetime import timedelta

from rest_framework import status

from api.models import *
from api.tests.test__base import LLAPITests, settings


class LaunchSLNv300Tests(LLAPITests):

    @unittest.skipIf(settings.IS_LL, "Not supported in this configuration.")
    def test_upcoming_normal(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test Normal endpoint
        path = '/3.0.0/launch/upcoming/?limit=1'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['count'], Launch.objects.filter(net__gte=timezone.now() - timedelta(days=1)).filter(launch_library=True).count())
        for data in data['results']:
            launch = Launch.objects.get(id=data['id'])
            self.assertEqual(data['id'], launch.launch_library_id)
            self.assertEqual(data['name'], launch.name)
            self.assertIsNotNone(data['isonet'])
            self.assertIsNotNone(data['netstamp'])

        self.check_permissions(path)

    @unittest.skipIf(settings.IS_LL, "Not supported in this configuration.")
    def test_upcoming_list(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test list endpoint
        path = '/3.0.0/launch/upcoming/?limit=1&mode=list'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['count'], Launch.objects.filter(net__gte=timezone.now() - timedelta(days=1)).filter(launch_library=True).count())
        for data in data['results']:
            launch = Launch.objects.get(id=data['id'])
            self.assertEqual(data['id'], launch.launch_library_id)
            self.assertEqual(data['name'], launch.name)
            self.assertNotIn('isonet', data)
            self.assertNotIn('netstamp', data)

        self.check_permissions(path)

    @unittest.skipIf(settings.IS_LL, "Not supported in this configuration.")
    def test_upcoming_detailed(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test detailed endpoint
        path = '/3.0.0/launch/upcoming/?limit=1&mode=detailed'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))

        self.assertEqual(data['count'], Launch.objects.filter(net__gte=timezone.now() - timedelta(days=1)).filter(launch_library=True).count())
        for data in data['results']:
            launch = Launch.objects.get(id=data['id'])
            self.assertEqual(data['id'], launch.launch_library_id)
            self.assertEqual(data['name'], launch.name)
            if data['lsp']:
                self.assertIn('founding_year', data['lsp'])

        self.check_permissions(path)

    @unittest.skipIf(settings.IS_LL, "Not supported in this configuration.")
    def test_previous_normal(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test Normal endpoint
        path = '/3.0.0/launch/previous/?limit=1'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['count'], Launch.objects.filter(net__lte=timezone.now()).filter(launch_library=True).count())
        for data in data['results']:
            self.assertIsNotNone(data['isonet'])
            self.assertIsNotNone(data['netstamp'])

        self.check_permissions(path)

    @unittest.skipIf(settings.IS_LL, "Not supported in this configuration.")
    def test_previous_list(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test list endpoint
        path = '/3.0.0/launch/previous/?limit=1&mode=list'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['count'], Launch.objects.filter(net__lte=timezone.now()).filter(launch_library=True).count())
        for data in data['results']:
            self.assertNotIn('isonet', data)
            self.assertNotIn('netstamp', data)

        self.check_permissions(path)

    @unittest.skipIf(settings.IS_LL, "Not supported in this configuration.")
    def test_previous_detailed(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test detailed endpoint
        path = '/3.0.0/launch/previous/?limit=1&mode=detailed'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['count'], Launch.objects.filter(net__lte=timezone.now()).filter(launch_library=True).count())
        for data in data['results']:
            self.assertIn('founding_year', data['lsp'])

        self.check_permissions(path)

    @unittest.skipIf(settings.IS_LL, "Not supported in this configuration.")
    def test_launch_with_landings(self):
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
        self.assertEqual(data['launcher']['id'], launch.rocket.configuration.launch_library_id)
        self.assertEqual(data['mission']['id'], launch.mission.launch_library_id)
        if launch.rocket.configuration.manufacturer:
            self.assertEqual(data['lsp']['id'], launch.rocket.configuration.manufacturer.id)
        self.assertEqual(data['location']['id'], launch.pad.location.launch_library_id)
        self.assertEqual(data['pad']['id'], launch.pad.launch_library_id)
