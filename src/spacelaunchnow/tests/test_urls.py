from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.authtoken.models import Token

from api.models import *
from api.tests.test__base import LLAPITests


class APITest(LLAPITests):

    @classmethod
    def setUpClass(cls):
        """ get_some_resource() is slow, to avoid calling it for each test use setUpClass()
            and store the result as class variable
        """
        super(LLAPITests, cls).setUpClass()
        cls.user, created = User.objects.get_or_create(username="Test User",
                                                       email="test@email.com",
                                                       password="testpassword")

        cls.group, create = Group.objects.get_or_create(name='unlimited_user')
        cls.user.groups.add(cls.group)
        cls.user.save()

        cls.token, created = Token.objects.get_or_create(user=cls.user)
        cls.header = {'Authorization': 'Token %s' % cls.token.key}

    def test_api_online(self):
        if settings.IS_API:
            path = '/3.0.0/'
            response = self.client.get(path)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            path = '/3.1.0/'
            response = self.client.get(path)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            path = '/3.2.0/'
            response = self.client.get(path)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            path = '/api/3.3.0/'
            response = self.client.get(path)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            path = '/api/3.4.0/'
            response = self.client.get(path)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            path = '/api/ll/2.0.0/'
            response = self.client.get(path)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            path = '/api/ll/2.1.0/'
            response = self.client.get(path)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            path = '/api/ll/2.2.0/'
            response = self.client.get(path)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            path = '/api/ll/2.2.0/swagger/'
            response = self.client.get(path)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            path = '/api/ll/2.2.0/redoc/'
            response = self.client.get(path)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            path = '/api/ll/2.2.0/new/swagger/'
            response = self.client.get(path)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            path = '/api/ll/2.2.0/new/schema/'
            response = self.client.get(path)
            self.assertEqual(response.status_code, status.HTTP_200_OK)