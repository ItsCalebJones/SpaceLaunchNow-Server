import json

from rest_framework import status
from rest_framework.test import APITestCase

from api.models import *
from bot.app.repository.launches_repository import LaunchRepository


class OrbiterTests(APITestCase):

    def setUp(self):
        self.repository = OrbiterTests.repository
        self.spacex = OrbiterTests.spacex
        self.dragon = OrbiterTests.dragon

    @classmethod
    def setUpClass(cls):
        """ get_some_resource() is slow, to avoid calling it for each test use setUpClass()
            and store the result as class variable
        """
        super(OrbiterTests, cls).setUpClass()
        cls.repository = LaunchRepository()
        cls.repository.get_launch_status()
        cls.repository.get_mission_type()
        cls.repository.get_agency_type()
        cls.spacex = Agency.objects.create(id=1,
                                           name="SpaceX",
                                           featured=True,
                                           country_code="USA",
                                           abbrev="SpX",
                                           type="Commercial",
                                           agency_type=AgencyType.objects.get(pk=3),
                                           description="This is a description",
                                           launchers="Do I use this?",
                                           orbiters="Do I use this?",
                                           administrator="Mr. Tesla",
                                           founding_year="2018", )
        cls.dragon = Orbiter.objects.create(id=1,
                                            name="Cargo Dragon",
                                            agency="SpaceX String",
                                            launch_agency=cls.spacex,
                                            history="This is a history.",
                                            details="This is a detail",
                                            in_use=False,
                                            capability="This is a capability",
                                            maiden_flight=None,
                                            height=12.0,
                                            diameter=10.0,
                                            human_rated=False,
                                            crew_capacity=None,
                                            payload_capacity=800,
                                            flight_life="One week.", )

    def test_v1_orbiters(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test Normal endpoint
        response = self.client.get('/v1/orbiters/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['id'], self.dragon.id)
        self.assertEqual(data['results'][0]['name'], self.dragon.name)
        self.assertEqual(data['results'][0]['agency'], self.dragon.launch_agency.name)
        self.assertEqual(data['results'][0]['nation_url'], self.dragon.nation_url)
        self.assertEqual(data['results'][0]['wiki_link'], self.dragon.wiki_link)
        self.assertEqual(data['results'][0]['image_url'], self.dragon.image_url)
        self.assertEqual(data['results'][0]['details'], self.dragon.details)
        self.assertEqual(data['results'][0]['history'], self.dragon.history)

    def test_v200_orbiters(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test Normal endpoint
        response = self.client.get('/2.0.0/orbiters/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['id'], self.dragon.id)
        self.assertEqual(data['results'][0]['name'], self.dragon.name)
        self.assertEqual(data['results'][0]['agency'], self.dragon.launch_agency.name)
        self.assertEqual(data['results'][0]['nation_url'], self.dragon.nation_url)
        self.assertEqual(data['results'][0]['wiki_link'], self.dragon.wiki_link)
        self.assertEqual(data['results'][0]['image_url'], self.dragon.image_url)
        self.assertEqual(data['results'][0]['details'], self.dragon.details)
        self.assertEqual(data['results'][0]['history'], self.dragon.history)
        self.assertEqual(data['results'][0]['in_use'], self.dragon.in_use)
        self.assertEqual(data['results'][0]['capability'], self.dragon.capability)

    def test_v300_orbiters(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test Normal endpoint
        response = self.client.get('/3.0.0/orbiters/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['id'], self.dragon.id)
        self.assertEqual(data['results'][0]['name'], self.dragon.name)
        self.assertEqual(data['results'][0]['agency'], self.dragon.launch_agency.name)
        self.assertEqual(data['results'][0]['nation_url'], self.dragon.nation_url)
        self.assertEqual(data['results'][0]['wiki_link'], self.dragon.wiki_link)
        self.assertEqual(data['results'][0]['image_url'], self.dragon.image_url)
        self.assertEqual(data['results'][0]['details'], self.dragon.details)
        self.assertEqual(data['results'][0]['history'], self.dragon.history)
        self.assertEqual(data['results'][0]['in_use'], self.dragon.in_use)
        self.assertEqual(data['results'][0]['capability'], self.dragon.capability)

    def test_v320_orbiters(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test Normal endpoint
        response = self.client.get('/3.2.0/orbiters/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['id'], self.dragon.id)
        self.assertEqual(data['results'][0]['name'], self.dragon.name)
        self.assertEqual(data['results'][0]['agency'], self.dragon.launch_agency.name)
        self.assertEqual(data['results'][0]['nation_url'], self.dragon.nation_url)
        self.assertEqual(data['results'][0]['wiki_link'], self.dragon.wiki_link)
        self.assertEqual(data['results'][0]['image_url'], self.dragon.image_url)
        self.assertEqual(data['results'][0]['details'], self.dragon.details)
        self.assertEqual(data['results'][0]['history'], self.dragon.history)
        self.assertEqual(data['results'][0]['in_use'], self.dragon.in_use)
        self.assertEqual(data['results'][0]['capability'], self.dragon.capability)
        self.assertEqual(data['results'][0]['maiden_flight'], self.dragon.maiden_flight)
        self.assertEqual(data['results'][0]['height'], self.dragon.height)
        self.assertEqual(data['results'][0]['diameter'], self.dragon.diameter)
        self.assertEqual(data['results'][0]['human_rated'], self.dragon.human_rated)
        self.assertEqual(data['results'][0]['crew_capacity'], self.dragon.crew_capacity)
        self.assertEqual(data['results'][0]['payload_capacity'], self.dragon.payload_capacity)
        self.assertEqual(data['results'][0]['flight_life'], self.dragon.flight_life)
