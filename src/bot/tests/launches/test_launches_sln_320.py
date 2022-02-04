import json
import unittest
from datetime import timedelta

from rest_framework import status

from api.models import *
from api.tests.test__base import LLAPITests, settings


class LaunchSLNv320Tests(LLAPITests):

    @unittest.skipIf(settings.IS_LL, "Not supported in this configuration.")
    def test_upcoming_normal(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test Normal endpoint
        path = '/3.2.0/launch/upcoming/?limit=1'
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
            self.assertIn('rocket', data)
            self.assertIn('net', data)
            self.assertIn('configuration', data['rocket'])
            self.assertIn('first_stage', data['rocket'])
            self.assertIn('pad', data)
            self.assertIn('location', data['pad'])

        self.check_permissions(path)

    @unittest.skipIf(settings.IS_LL, "Not supported in this configuration.")
    def test_upcoming_list(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test list endpoint
        path = '/3.2.0/launch/upcoming/?limit=1&mode=list'
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
            self.assertNotIn('rocket', data)
            self.assertIn('name', data['status'])
            self.assertIn('name', data)
            self.assertIn('net', data)
            self.assertIn('pad', data)
            self.assertIn('landing', data)
            self.assertIn('orbit', data)

        self.check_permissions(path)

    @unittest.skipIf(settings.IS_LL, "Not supported in this configuration.")
    def test_upcoming_detailed(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test detailed endpoint
        path = '/3.2.0/launch/upcoming/?limit=1&mode=detailed'
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
            self.assertIn('rocket', data)
            self.assertIn('net', data)
            self.assertIn('configuration', data['rocket'])
            self.assertIn('diameter', data['rocket']['configuration'])
            self.assertIn('first_stage', data['rocket'])
            self.assertIn('pad', data)
            self.assertIn('location', data['pad'])

        self.check_permissions(path)

    @unittest.skipIf(settings.IS_LL, "Not supported in this configuration.")
    def test_previous_normal(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test Normal endpoint
        path = '/3.2.0/launch/previous/?limit=1'
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
            self.assertIn('rocket', data)
            self.assertIn('net', data)
            self.assertIn('configuration', data['rocket'])
            self.assertIn('first_stage', data['rocket'])
            self.assertIn('pad', data)
            self.assertIn('location', data['pad'])

        self.check_permissions(path)

    @unittest.skipIf(settings.IS_LL, "Not supported in this configuration.")
    def test_previous_list(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test list endpoint
        path = '/3.2.0/launch/previous/?limit=1&mode=list'
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
            self.assertNotIn('rocket', data)
            self.assertIn('name', data['status'])
            self.assertIn('name', data)
            self.assertIn('net', data)
            self.assertIn('pad', data)
            self.assertIn('landing', data)
            self.assertIn('orbit', data)

        self.check_permissions(path)

    @unittest.skipIf(settings.IS_LL, "Not supported in this configuration.")
    def test_previous_detailed(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test detailed endpoint
        path = '/3.2.0/launch/previous/?limit=1&mode=detailed'
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
            self.assertIn('rocket', data)
            self.assertIn('net', data)
            self.assertIn('configuration', data['rocket'])
            self.assertIn('diameter', data['rocket']['configuration'])
            self.assertIn('first_stage', data['rocket'])
            self.assertIn('pad', data)
            self.assertIn('location', data['pad'])

        self.check_permissions(path)

    @unittest.skipIf(settings.IS_LL, "Not supported in this configuration.")
    def test_launch_with_landings(self):
        launch = Launch.objects.get(launch_library_id=864)

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
        self.assertEqual(data['rocket']['configuration']['id'], launch.rocket.configuration.launch_library_id)
        self.assertEqual(data['rocket']['configuration']['launch_service_provider'], launch.rocket.configuration.manufacturer.name)
        self.assertEqual(len(data['rocket']['first_stage']), launch.rocket.firststage.count())
        for index, stage_data in enumerate(data['rocket']['first_stage']):
            stage = launch.rocket.firststage.all().order_by('id')[index]
            self.assertEqual(stage_data['type'], stage.type.name)
            self.assertEqual(stage_data['reused'], stage.reused)
            self.assertEqual(stage_data['launcher_flight_number'], stage.launcher_flight_number)
            self.assertEqual(stage_data['launcher']['id'], stage.launcher.id)
            self.assertEqual(stage_data['launcher']['serial_number'], stage.launcher.serial_number)
            self.assertEqual(stage_data['landing']['attempt'], stage.landing.attempt)
            self.assertEqual(stage_data['landing']['success'], stage.landing.success)
            self.assertEqual(stage_data['landing']['description'], stage.landing.description)
            self.assertEqual(stage_data['landing']['location']['name'], stage.landing.landing_location.name)
            self.assertEqual(stage_data['landing']['type']['name'], stage.landing.landing_type.name)
        self.assertEqual(data['mission']['id'], launch.mission.launch_library_id)
        self.assertEqual(data['pad']['id'], launch.pad.launch_library_id)
        self.assertEqual(data['pad']['location']['id'], launch.pad.location.launch_library_id)

