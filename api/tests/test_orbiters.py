import json

from rest_framework import status

from api.models import SpacecraftConfiguration
from api.tests.test__base import SLNAPITests


class OrbiterTests(SLNAPITests):

    def test_v1_orbiters(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test Normal endpoint

        path = '/v1/orbiters/'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['count'], 1)
        dragon = SpacecraftConfiguration.objects.get(pk=data['results'][0]['id'])
        self.assertEqual(data['results'][0]['id'], dragon.id)
        self.assertEqual(data['results'][0]['name'], dragon.name)
        self.assertEqual(data['results'][0]['agency'], dragon.launch_agency.name)
        self.assertEqual(data['results'][0]['details'], dragon.details)
        self.assertEqual(data['results'][0]['history'], dragon.history)

        self.check_permissions(path)

    def test_v200_orbiters(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test Normal endpoint
        path = '/2.0.0/orbiters/'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['count'], 1)
        dragon = SpacecraftConfiguration.objects.get(pk=data['results'][0]['id'])
        self.assertEqual(data['results'][0]['id'], dragon.id)
        self.assertEqual(data['results'][0]['name'], dragon.name)
        self.assertEqual(data['results'][0]['agency'], dragon.launch_agency.name)
        self.assertEqual(data['results'][0]['details'], dragon.details)
        self.assertEqual(data['results'][0]['history'], dragon.history)
        self.assertEqual(data['results'][0]['in_use'], dragon.in_use)
        self.assertEqual(data['results'][0]['capability'], dragon.capability)

        self.check_permissions(path)

    def test_v300_orbiters(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test Normal endpoint
        path = '/3.0.0/orbiters/'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['count'], 1)
        dragon = SpacecraftConfiguration.objects.get(pk=data['results'][0]['id'])
        self.assertEqual(data['results'][0]['id'], dragon.id)
        self.assertEqual(data['results'][0]['name'], dragon.name)
        self.assertEqual(data['results'][0]['agency'], dragon.launch_agency.name)
        self.assertEqual(data['results'][0]['details'], dragon.details)
        self.assertEqual(data['results'][0]['history'], dragon.history)
        self.assertEqual(data['results'][0]['capability'], dragon.capability)

        self.check_permissions(path)

    def test_v320_orbiters(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test Normal endpoint
        path = '/3.2.0/orbiters/'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['count'], 1)
        dragon = SpacecraftConfiguration.objects.get(pk=data['results'][0]['id'])
        self.assertEqual(data['results'][0]['id'], dragon.id)
        self.assertEqual(data['results'][0]['name'], dragon.name)
        self.assertEqual(data['results'][0]['agency'], dragon.launch_agency.name)
        self.assertEqual(data['results'][0]['details'], dragon.details)
        self.assertEqual(data['results'][0]['history'], dragon.history)
        self.assertEqual(data['results'][0]['in_use'], dragon.in_use)
        self.assertEqual(data['results'][0]['capability'], dragon.capability)
        self.assertEqual(data['results'][0]['maiden_flight'], dragon.maiden_flight)
        self.assertEqual(data['results'][0]['height'], dragon.height)
        self.assertEqual(data['results'][0]['diameter'], dragon.diameter)
        self.assertEqual(data['results'][0]['human_rated'], dragon.human_rated)
        self.assertEqual(data['results'][0]['crew_capacity'], dragon.crew_capacity)
        self.assertEqual(data['results'][0]['payload_capacity'], dragon.payload_capacity)
        self.assertEqual(data['results'][0]['flight_life'], dragon.flight_life)

        self.check_permissions(path)

    def test_v330_orbiters(self):
        """
        Ensure orbiter endpoints work as expected. Now config.
        """
        path = '/api/3.3.0/config/spacecraft/?mode=detailed'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['count'], 1)
        dragon = SpacecraftConfiguration.objects.get(pk=data['results'][0]['id'])
        self.assertEqual(data['results'][0]['id'], dragon.id)
        self.assertEqual(data['results'][0]['name'], dragon.name)
        self.assertEqual(data['results'][0]['agency'], dragon.launch_agency.name)
        self.assertEqual(data['results'][0]['details'], dragon.details)
        self.assertEqual(data['results'][0]['history'], dragon.history)
        self.assertEqual(data['results'][0]['in_use'], dragon.in_use)
        self.assertEqual(data['results'][0]['capability'], dragon.capability)
        self.assertEqual(data['results'][0]['maiden_flight'], dragon.maiden_flight)
        self.assertEqual(data['results'][0]['height'], dragon.height)
        self.assertEqual(data['results'][0]['diameter'], dragon.diameter)
        self.assertEqual(data['results'][0]['human_rated'], dragon.human_rated)
        self.assertEqual(data['results'][0]['crew_capacity'], dragon.crew_capacity)
        self.assertEqual(data['results'][0]['payload_capacity'], dragon.payload_capacity)
        self.assertEqual(data['results'][0]['flight_life'], dragon.flight_life)

        self.check_permissions(path)
