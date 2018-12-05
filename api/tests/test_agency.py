import json

from rest_framework import status

from api.models import *
from api.tests.test__base import SLNAPITests


class AgencyTests(SLNAPITests):

    def test_v1_agency(self):
        """
        Ensure Agency endpoints work as expected.
        """
        # Test Normal endpoint
        path = '/v1/agency/'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['count'], Agency.objects.filter(featured=True).count())
        self.assertIn('url', data['results'][0])
        self.assertIn('agency', data['results'][0])
        self.assertIn('launchers', data['results'][0])
        self.assertIn('orbiters', data['results'][0])
        if len(data['results'][0]['launcher_list']) > 0:
            self.assertIn('id', data['results'][0]['launcher_list'][0])
            self.assertIn('url', data['results'][0]['launcher_list'][0])
            self.assertIn('name', data['results'][0]['launcher_list'][0])
            self.assertIn('description', data['results'][0]['launcher_list'][0])
            self.assertIn('agency', data['results'][0]['launcher_list'][0])
            self.assertIn('variant', data['results'][0]['launcher_list'][0])
            self.assertIn('image_url', data['results'][0]['launcher_list'][0])
            self.assertIn('info_url', data['results'][0]['launcher_list'][0])
            self.assertIn('wiki_url', data['results'][0]['launcher_list'][0])

        self.check_permissions(path)

    def test_v200_agency(self):
        """
        Ensure Agency endpoints work as expected.
        """
        # Test Normal endpoint
        path = '/2.0.0/agencies/'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(data['count'], Agency.objects.all().count())
        agency = Agency.objects.get(pk=data['results'][0]['id'])
        self.assertEqual(data['results'][0]['id'], agency.id)
        self.assertEqual(data['results'][0]['name'], agency.name)
        self.assertEqual(data['results'][0]['featured'], agency.featured)
        self.assertEqual(data['results'][0]['launchers'], agency.launchers)
        self.assertEqual(data['results'][0]['orbiters'], agency.spacecraft)
        self.assertIn('launcher_list', data['results'][0])
        self.assertIn('orbiter_list', data['results'][0])
        self.assertEqual(data['results'][0]['description'], agency.description)
        self.assertEqual(data['results'][0]['ceo'], agency.administrator)
        self.assertEqual(data['results'][0]['founding_year'], agency.founding_year)

        if len(data['results'][0]['launcher_list']) > 0:
            self.assertIn('id', data['results'][0]['launcher_list'][0])
            self.assertIn('url', data['results'][0]['launcher_list'][0])
            self.assertIn('name', data['results'][0]['launcher_list'][0])
            self.assertIn('description', data['results'][0]['launcher_list'][0])
            self.assertIn('agency', data['results'][0]['launcher_list'][0])
            self.assertIn('variant', data['results'][0]['launcher_list'][0])
            self.assertIn('image_url', data['results'][0]['launcher_list'][0])
            self.assertIn('info_url', data['results'][0]['launcher_list'][0])
            self.assertIn('wiki_url', data['results'][0]['launcher_list'][0])

        self.check_permissions(path)

    def test_v300_agency(self):
        """
        Ensure Agency endpoints work as expected.
        """
        # Test Normal endpoint
        path = '/3.0.0/agencies/'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))

        self.assertEqual(data['count'], Agency.objects.all().count())
        agency = Agency.objects.get(pk=data['results'][0]['id'])
        self.assertEqual(data['results'][0]['id'], agency.id)
        self.assertEqual(data['results'][0]['name'], agency.name)
        self.assertEqual(data['results'][0]['featured'], agency.featured)
        self.assertEqual(data['results'][0]['launchers'], agency.launchers)
        self.assertEqual(data['results'][0]['orbiters'], agency.spacecraft)
        self.assertEqual(data['results'][0]['description'], agency.description)
        self.assertEqual(data['results'][0]['administrator'], agency.administrator)
        self.assertEqual(data['results'][0]['founding_year'], agency.founding_year)
        self.assertEqual(data['results'][0]['type'], agency.agency_type.name)

        self.check_permissions(path)

    def test_v300_agency_detailed(self):
        """
        Ensure Agency endpoints work as expected.
        """
        # Test Normal endpoint
        path = '/3.0.0/agencies/?mode=detailed'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))

        self.assertEqual(data['count'], Agency.objects.all().count())
        agency = Agency.objects.get(pk=data['results'][0]['id'])
        self.assertEqual(data['results'][0]['id'], agency.id)
        self.assertEqual(data['results'][0]['name'], agency.name)
        self.assertEqual(data['results'][0]['featured'], agency.featured)
        self.assertEqual(data['results'][0]['launchers'], agency.launchers)
        self.assertEqual(data['results'][0]['orbiters'], agency.spacecraft)
        self.assertEqual(data['results'][0]['description'], agency.description)
        self.assertEqual(data['results'][0]['administrator'], agency.administrator)
        self.assertEqual(data['results'][0]['founding_year'], agency.founding_year)
        self.assertEqual(data['results'][0]['type'], agency.agency_type.name)
        self.assertIn('orbiter_list', data['results'][0])
        self.assertIn('launcher_list', data['results'][0])

        self.check_permissions(path)

    def test_v320_agency(self):
        """
        Ensure Agency endpoints work as expected.
        """
        # Test Normal endpoint
        path = '/3.2.0/agencies/'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))

        self.assertEqual(data['count'], Agency.objects.all().count())
        agency = Agency.objects.get(pk=data['results'][0]['id'])
        self.assertEqual(data['results'][0]['id'], agency.id)
        self.assertEqual(data['results'][0]['name'], agency.name)
        self.assertEqual(data['results'][0]['featured'], agency.featured)
        self.assertEqual(data['results'][0]['country_code'], agency.country_code)
        self.assertEqual(data['results'][0]['abbrev'], agency.abbrev)
        self.assertEqual(data['results'][0]['launchers'], agency.launchers)
        self.assertEqual(data['results'][0]['orbiters'], agency.spacecraft)
        self.assertEqual(data['results'][0]['description'], agency.description)
        self.assertEqual(data['results'][0]['administrator'], agency.administrator)
        self.assertEqual(data['results'][0]['founding_year'], agency.founding_year)
        self.assertEqual(data['results'][0]['type'], agency.agency_type.name)

        self.check_permissions(path)

    def test_v320_agency_detailed(self):
        """
        Ensure Agency endpoints work as expected.
        """
        # Test Normal endpoint
        path = '/3.2.0/agencies/?mode=detailed'
        response = self.client.get(path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode('utf-8'))

        self.assertEqual(data['count'], Agency.objects.all().count())
        agency = Agency.objects.get(pk=data['results'][0]['id'])
        self.assertEqual(data['results'][0]['id'], agency.id)
        self.assertEqual(data['results'][0]['name'], agency.name)
        self.assertEqual(data['results'][0]['featured'], agency.featured)
        self.assertEqual(data['results'][0]['country_code'], agency.country_code)
        self.assertEqual(data['results'][0]['abbrev'], agency.abbrev)
        self.assertEqual(data['results'][0]['launchers'], agency.launchers)
        self.assertEqual(data['results'][0]['orbiters'], agency.spacecraft)
        self.assertEqual(data['results'][0]['description'], agency.description)
        self.assertEqual(data['results'][0]['administrator'], agency.administrator)
        self.assertEqual(data['results'][0]['founding_year'], agency.founding_year)
        self.assertEqual(data['results'][0]['type'], agency.agency_type.name)
        self.assertIn('orbiter_list', data['results'][0])
        self.assertIn('launcher_list', data['results'][0])

        self.check_permissions(path)
