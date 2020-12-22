import json
import unittest

from rest_framework import status

from api.models import SpaceStation
from api.tests.test__base import LLAPITests
from spacelaunchnow import settings


class SpaceStationTest(LLAPITests):

    @unittest.skipIf(settings.IS_LL, "Not supported in this configuration.")
    def test_v330_spacestations(self):
        """
        Ensure spacestation endpoints work as expected.
        """
        path = '/api/3.3.0/spacestation/'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['count'], 1)
        iss = SpaceStation.objects.get(name=data['results'][0]['name'])
        self.assertEqual(data['results'][0]['name'], iss.name)
        self.assertEqual(data['results'][0]['founded'], "1998-11-20")
        self.assertEqual(data['results'][0]['description'], iss.description)
        self.assertEqual(data['results'][0]['orbit'], iss.orbit.name)

    @unittest.skipIf(settings.IS_LL, "Not supported in this configuration.")
    def test_v330_spacestations_detailed(self):
        """
        Ensure spacestation endpoints work as expected.
        """
        path = '/api/3.3.0/spacestation/?mode=detailed'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['count'], 1)
        iss = SpaceStation.objects.get(name=data['results'][0]['name'])
        self.assertEqual(data['results'][0]['name'], iss.name)
        self.assertEqual(data['results'][0]['founded'], "1998-11-20")
        self.assertEqual(data['results'][0]['description'], iss.description)
        self.assertEqual(data['results'][0]['orbit'], iss.orbit.name)
        self.assertIn('owners', data['results'][0])
        self.assertIn('docked_vehicles', data['results'][0])
        self.assertIn('active_expeditions', data['results'][0])
