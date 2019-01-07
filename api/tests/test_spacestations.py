import json

from rest_framework import status

from api.models import SpaceStation
from api.tests.test__base import SLNAPITests


class SpaceStationTest(SLNAPITests):

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
        self.assertEqual(data['results'][0]['orbit'], iss.orbit)
        self.assertEqual(data['results'][0]['crew'][0]['name'],
                         iss.crew.all()[0].name)
        self.assertEqual(data['results'][0]['status']['name'],
                         iss.status.name)
        self.assertEqual(data['results'][0]['owner']['name'],
                         iss.owner.name)
