import json

import pytz
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from api.models import *
from bot.app.repository.launches_repository import LaunchRepository


def setUpModule():
    print("Initializing Test Data")
    repository = LaunchRepository()
    repository.get_launch_status()
    repository.get_mission_type()
    repository.get_agency_type()
    repository.get_launch_by_id(864)
    repository.get_launch_by_id(998)
    repository.get_next_launches(2)

    spacex = Agency.objects.create(id=1,
                                   name="SpaceX",
                                   featured=True,
                                   country_code="USA",
                                   abbrev="SpX",
                                   type="Commercial",
                                   agency_type=AgencyType.objects.get(pk=3),
                                   description="This is a description",
                                   launchers="Do I use this?",
                                   spacecraft="Do I use this?",
                                   administrator="Mr. Tesla",
                                   founding_year="2018", )
    launcher_config = LauncherConfig.objects.create(id=10000001,
                                                    name="Falcon 9",
                                                    active=True,
                                                    reusable=True,
                                                    audited=False,
                                                    librarian_notes="",
                                                    description="This description",
                                                    family="Falcon",
                                                    full_name="Falcon 9 Full Thrust",
                                                    launch_agency=spacex,
                                                    variant="Full Thrust",
                                                    alias="Some Alias",
                                                    launch_cost="120",
                                                    maiden_flight=None,
                                                    min_stage=1,
                                                    max_stage=2,
                                                    length=10.0,
                                                    diameter=10.1,
                                                    fairing_diameter=5.0,
                                                    launch_mass=100,
                                                    leo_capacity=125,
                                                    gto_capacity=150,
                                                    geo_capacity=175,
                                                    sso_capacity=200,
                                                    to_thrust=100,
                                                    apogee=100,
                                                    vehicle_range=None, )
    Launcher.objects.create(id=1,
                            serial_number="Test",
                            flight_proven=True,
                            status="Some asinine status",
                            details="This weird little detail",
                            launcher_config=launcher_config)
    SpacecraftConfiguration.objects.create(id=1,
                                           name="Cargo Dragon",
                                           agency="SpaceX String",
                                           launch_agency=spacex,
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
    astro_status = AstronautStatus.objects.create(name='Active')
    starman = Astronaut.objects.create(name="Starman",
                                       date_of_birth=datetime.datetime.strptime(
                                            '06/02/2018',
                                            '%d/%m/%Y'),
                                       status=astro_status,
                                       nationality='American',
                                       agency=spacex,
                                       twitter="SpaceX",
                                       bio="Driver of a cherry red roadster")
    iss_status = SpaceStationStatus.objects.create(name='Active')
    orbit, created = Orbit.objects.get_or_create(name="Low Earth Orbit",
                                        abbrev="LEO")
    iss = SpaceStation.objects.create(id=1,
                                      name="ISS",
                                      founded=datetime.datetime.strptime(
                                          '20/11/1998',
                                          '%d/%m/%Y'),
                                      status=iss_status,
                                      description="International Station",
                                      orbit=orbit)
    iss.owners.add(spacex)


class SLNAPITests(APITestCase):

    @classmethod
    def setUpClass(cls):
        """ get_some_resource() is slow, to avoid calling it for each test use setUpClass()
            and store the result as class variable
        """
        super(SLNAPITests, cls).setUpClass()
        cls.user, created = User.objects.get_or_create(username="Test User",
                                                       email="test@email.com",
                                                       password="testpassword")
        cls.token, created = Token.objects.get_or_create(user=cls.user)
        cls.header = {'Authorization': 'Token %s' % cls.token.key}

    def test_api_online(self):
        path = '/v1/'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        path = '/2.0.0/'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        path = '/3.0.0/'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        path = '/3.1.0/'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        path = '/3.2.0/'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def check_permissions(self, path):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.post(path, **self.header)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.delete(path, **self.header)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.credentials()
        response = self.client.post(path)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.delete(path)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
