import json
import unittest
from datetime import timedelta

from rest_framework import status

from api.models import *
from api.tests.test__base import LLAPITests, settings


class LaunchSLNv310Tests(LLAPITests):

    @unittest.skipIf(settings.IS_LL, "Not supported in this configuration.")
    def test_upcoming_normal(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test Normal endpoint
        path = '/3.1.0/launch/upcoming/?limit=1'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['count'], Launch.objects.filter(net__gte=timezone.now() - timedelta(days=1)).filter(launch_library=True).count())
        for data in data['results']:
            launch = Launch.objects.get(launch_library_id=data['id'])
            self.assertEqual(data['id'], launch.launch_library_id)
            self.assertEqual(data['name'], launch.name)
            self.assertNotIn('netstamp', data)
            self.assertNotIn('isonet', data)
            self.assertIn('name', data['status'])

        self.check_permissions(path)

    @unittest.skipIf(settings.IS_LL, "Not supported in this configuration.")
    def test_upcoming_list(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test list endpoint
        path = '/3.1.0/launch/upcoming/?limit=1&mode=list'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['count'], Launch.objects.filter(net__gte=timezone.now() - timedelta(days=1)).filter(launch_library=True).count())
        for data in data['results']:
            launch = Launch.objects.get(launch_library_id=data['id'])
            self.assertEqual(data['id'], launch.launch_library_id)
            self.assertEqual(data['name'], launch.name)
            self.assertNotIn('netstamp', data)
            self.assertNotIn('isonet', data)
            self.assertIn('name', data['status'])

        self.check_permissions(path)

    @unittest.skipIf(settings.IS_LL, "Not supported in this configuration.")
    def test_upcoming_detailed(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test detailed endpoint
        path = '/3.1.0/launch/upcoming/?limit=1&mode=detailed'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['count'], Launch.objects.filter(net__gte=timezone.now() - timedelta(days=1)).filter(launch_library=True).count())
        for data in data['results']:
            launch = Launch.objects.get(launch_library_id=data['id'])
            self.assertEqual(data['id'], launch.launch_library_id)
            self.assertEqual(data['name'], launch.name)
            self.assertNotIn('netstamp', data)
            self.assertNotIn('isonet', data)
            self.assertIn('name', data['status'])
            if data['lsp']:
                self.assertIn('founding_year', data['lsp'])

        self.check_permissions(path)

    @unittest.skipIf(settings.IS_LL, "Not supported in this configuration.")
    def test_previous_normal(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test Normal endpoint
        path = '/3.1.0/launch/previous/?limit=1'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['count'], Launch.objects.filter(net__lte=timezone.now()).filter(launch_library=True).count())
        for data in data['results']:
            launch = Launch.objects.get(launch_library_id=data['id'])
            self.assertEqual(data['id'], launch.launch_library_id)
            self.assertEqual(data['name'], launch.name)
            self.assertNotIn('netstamp', data)
            self.assertNotIn('isonet', data)
            self.assertIn('name', data['status'])

        self.check_permissions(path)

    @unittest.skipIf(settings.IS_LL, "Not supported in this configuration.")
    def test_previous_list(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test list endpoint
        path = '/3.1.0/launch/previous/?limit=1&mode=list'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['count'], Launch.objects.filter(net__lte=timezone.now()).filter(launch_library=True).count())
        for data in data['results']:
            launch = Launch.objects.get(launch_library_id=data['id'])
            self.assertEqual(data['id'], launch.launch_library_id)
            self.assertEqual(data['name'], launch.name)
            self.assertNotIn('netstamp', data)
            self.assertNotIn('isonet', data)
            self.assertIn('name', data['status'])

        self.check_permissions(path)

    @unittest.skipIf(settings.IS_LL, "Not supported in this configuration.")
    def test_previous_detailed(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test detailed endpoint
        path = '/3.1.0/launch/previous/?limit=1&mode=detailed'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['count'], Launch.objects.filter(net__lte=timezone.now()).filter(launch_library=True).count())
        for data in data['results']:
            launch = Launch.objects.get(launch_library_id=data['id'])
            self.assertEqual(data['id'], launch.launch_library_id)
            self.assertEqual(data['name'], launch.name)
            self.assertNotIn('netstamp', data)
            self.assertNotIn('isonet', data)
            self.assertIn('founding_year', data['lsp'])
            self.assertIn('name', data['status'])

        self.check_permissions(path)

    @unittest.skipIf(settings.IS_LL, "Not supported in this configuration.")
    def test_launch_with_landings(self):
        launch = Launch.objects.get(launch_library_id=864)
        path = '/3.1.0/launch/864/'
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

