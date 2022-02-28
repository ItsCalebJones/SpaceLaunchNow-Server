import json
import unittest

from rest_framework import status

from api.models import Agency
from api.tests.test__base import LLAPITests, settings


class AgencySLN300Tests(LLAPITests):

    @unittest.skipIf(settings.IS_LL, "Not supported in this configuration.")
    def test_sln_v300_agency(self):
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

    @unittest.skipIf(settings.IS_LL, "Not supported in this configuration.")
    def test_sln_v300_agency_detailed(self):
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
