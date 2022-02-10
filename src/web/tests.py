# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from api.tests.test__base import LLAPITests
from django.test import TestCase

# Create your tests here.
from rest_framework import status

from bot.app.repository.launches_repository import LaunchRepository


class WebTests(LLAPITests):

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
