
from rest_framework import status
from rest_framework.authtoken.models import Token

from api.models import *
from api.tests.test__base import LLAPITests


class SLNAPITest(LLAPITests):

    @classmethod
    def setUpClass(cls):
        """ get_some_resource() is slow, to avoid calling it for each test use setUpClass()
            and store the result as class variable
        """
        super(LLAPITests, cls).setUpClass()
        cls.user, created = User.objects.get_or_create(username="Test User",
                                                       email="test@email.com",
                                                       password="testpassword")
        cls.token, created = Token.objects.get_or_create(user=cls.user)
        cls.header = {'Authorization': 'Token %s' % cls.token.key}

    def test_sln_300_api_online(self):
            path = '/3.0.0/'
            response = self.client.get(path)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_sln_310_api_online(self):
            path = '/3.1.0/'
            response = self.client.get(path)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_sln_320_api_online(self):
            path = '/3.2.0/'
            response = self.client.get(path)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_sln_330_api_online(self):
            path = '/api/3.3.0/'
            response = self.client.get(path)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_sln_340_api_online(self):
            path = '/api/3.4.0/'
            response = self.client.get(path)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_ll_200_api_online(self):
            path = '/api/ll/2.0.0/'
            response = self.client.get(path)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_ll_210_api_online(self):
            path = '/api/ll/2.1.0/'
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