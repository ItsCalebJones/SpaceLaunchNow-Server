# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase

# Create your tests here.
from rest_framework import status

from bot.app.repository.launches_repository import LaunchRepository


class WebTests(TestCase):
    def setUp(self):
        self.repository = WebTests.repository
        self.launches = WebTests.launches

    @classmethod
    def setUpClass(cls):
        """ get_some_resource() is slow, to avoid calling it for each test use setUpClass()
            and store the result as class variable
        """
        super(WebTests, cls).setUpClass()
        cls.repository = LaunchRepository()
        cls.repository.get_launch_status()
        cls.repository.get_mission_type()
        cls.repository.get_agency_type()
        cls.repository.get_launch_by_id(864)
        cls.repository.get_launch_by_id(998)
        cls.launches = cls.repository.get_next_launches(5)

    def test_home(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test Normal endpoint
        response = self.client.get('/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_next(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test Normal endpoint
        response = self.client.get('/next/')
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_launches(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test Normal endpoint
        response = self.client.get('/launch/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_launch_by_id(self):
        """
        Ensure launch endpoints work as expected.
        """
        # Test Normal endpoint
        response = self.client.get('/launch/%d' % self.launches[0].id)
        self.assertEqual(response.status_code, status.HTTP_301_MOVED_PERMANENTLY)
