import requests
import logging
from datetime import timedelta
from django.utils.datetime_safe import datetime

logger = logging.getLogger('bot.notifications')

BASE_URL = 'https://launchlibrary.net/'
headers = {
    "Content-Type": "application/json"
}


class LaunchLibrarySDK(object):
    # Latest stable Version stored.
    def __init__(self, version='1.4'):
        if version is None:
            version = '1.4'
        self.version = version
        self.api_url = BASE_URL + self.version

    def get_next_launch(self, tbd=False, launch_service_provider=None, count=1):
        """
        Builds a URL and fetches response from LL
        :param agency: Pass the ID of an Agency to get launches for that agency (Rocket, Location, or Mission agency)
        :param launch_service_provider: Pass the ID of a LSP to get launches for that provider
        :param count: The number of launch objects to fetch.
        :return: Returns a HTTP Response object
        """
        if 'dev' not in self.version:
            url = self.api_url + '/launch/next/%d?mode=verbose&tbdtime=0&tbddate=0' % count
        else:
            url = self.api_url + '/launch/next/%d?mode=verbose' % count

        if launch_service_provider:
            url = url + "&lsp=" + launch_service_provider
        return send_request(url, method='GET', headers=headers)

    def get_next_weeks_launches(self):
        """
        Sends a request using `requests` module.
        :return: Returns a HTTP Response object
        """
        today = datetime.today().strftime('%Y-%m-%d')
        next_week = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        url = self.api_url + '/launch/%s/%s?mode=verbose' % (today, next_week)
        return send_request(url, method='GET', headers=headers)

    def get_location_by_pad(self, location_id):
        url = '%s/pad/%i?fields=name' % (self.api_url, location_id)
        return send_request(url, method='GET', headers=headers)

    def get_launch_by_id(self, launch_id):
        url = self.api_url + '/launch/%s?mode=verbose' % launch_id
        return send_request(url, method='GET', headers=headers)


def send_request(url, method='GET', data=None, headers=None):
    """
    Sends a request using `requests` module.
    :param url: URL to send request to
    :param method: HTTP method to use e.g. GET, PUT, DELETE, POST
    :param data: Data to send in case of PUT and POST
    :param headers: HTTP headers to use
    :return: Returns a HTTP Response object
    """
    assert url and method
    assert method in ['GET', 'PUT', 'DELETE', 'POST']
    method = getattr(requests, method.lower())
    response = method(url=url, data=data, headers=headers)
    return response
