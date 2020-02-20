import json

from rest_framework import status

from api.models import *
from bot.tests.test__base import SLNAPITests


class LauncherTests(SLNAPITests):

    def test_v320_launcher(self):
        """
        Ensure Launcher endpoints work as expected.
        """
        path = '/3.2.0/launcher/'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['count'], Agency.objects.filter(featured=True).count())
        self.assertIn('id', data['results'][0])
        launcher = Launcher.objects.get(pk=data['results'][0]['id'])
        self.assertEqual(data['results'][0]['details'], launcher.details)
        self.assertEqual(data['results'][0]['flight_proven'], launcher.flight_proven)
        self.assertEqual(data['results'][0]['serial_number'], launcher.serial_number)
        self.assertEqual(data['results'][0]['previous_flights'], launcher.flights)

        self.check_permissions(path)

    def test_v330_launcher(self):
        """
        Ensure Launcher endpoints work as expected.
        """
        path = '/api/3.3.0/launcher/'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['count'], Agency.objects.filter(featured=True).count())
        self.assertIn('id', data['results'][0])
        launcher = Launcher.objects.get(pk=data['results'][0]['id'])
        self.assertEqual(data['results'][0]['details'], launcher.details)
        self.assertEqual(data['results'][0]['flight_proven'], launcher.flight_proven)
        self.assertEqual(data['results'][0]['serial_number'], launcher.serial_number)
        self.assertIn('launcher_config', data['results'][0])
        self.assertEqual(data['results'][0]['previous_flights'], launcher.flights)

        self.check_permissions(path)

    def test_v330_launcher_detailed(self):
        """
        Ensure Launcher endpoints work as expected.
        """
        path = '/api/3.3.0/launcher/?mode=detailed'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['count'], Agency.objects.filter(featured=True).count())
        self.assertIn('id', data['results'][0])
        launcher = Launcher.objects.get(pk=data['results'][0]['id'])
        self.assertEqual(data['results'][0]['details'], launcher.details)
        self.assertEqual(data['results'][0]['flight_proven'], launcher.flight_proven)
        self.assertEqual(data['results'][0]['serial_number'], launcher.serial_number)
        self.assertIn('launcher_config', data['results'][0])
        self.assertEqual(data['results'][0]['previous_flights'], launcher.flights)

        self.check_permissions(path)

    def test_v340_launcher_detailed(self):
        """
        Ensure Launcher endpoints work as expected.
        """
        path = '/api/3.4.0/launcher/?mode=detailed'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['count'], Agency.objects.filter(featured=True).count())
        self.assertIn('id', data['results'][0])
        launcher = Launcher.objects.get(pk=data['results'][0]['id'])
        self.assertEqual(data['results'][0]['details'], launcher.details)
        self.assertEqual(data['results'][0]['flight_proven'], launcher.flight_proven)
        self.assertEqual(data['results'][0]['serial_number'], launcher.serial_number)
        self.assertIn('launcher_config', data['results'][0])
        self.assertEqual(data['results'][0]['flights'], launcher.flights)

        self.check_permissions(path)
