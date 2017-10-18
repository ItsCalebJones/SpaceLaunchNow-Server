import requests
from datetime import timedelta
from django.utils.datetime_safe import datetime

BASE_URL = 'https://launchlibrary.net/'
headers = {
    "Content-Type": "application/json"
}


class LaunchLibrarySDK(object):
    def __init__(self, version='1.2.2'):
        self.api_url = BASE_URL + version

    def get_next_launches(self, number_launches=5, search=None):
        if search is None:
            url = self.api_url + '/launch/next/%d?mode=verbose&tbdtime=0&tbddate=0' % number_launches
        else:
            url = self.api_url + '/launch/next/%d?mode=verbose&name=%s&tbdtime=0&tbddate=0' %\
                                 (number_launches, search)
        return send_request(url, method='GET', headers=headers)

    def get_next_launch(self):
        url = self.api_url + '/launch/next/1&mode=verbose'
        return send_request(url, method='GET', headers=headers)

    def get_next_weeks_launches(self):
        today = datetime.today().strftime('%Y-%m-%d')
        next_week = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        url = self.api_url + '/launch/%s/%s?mode=verbose' % (today, next_week)
        return send_request(url, method='GET', headers=headers)

    def get_location_by_pad(self, locationId):
        url = '%s/pad/%i?fields=name' % (self.api_url, locationId)
        return send_request(url, method='GET', headers=headers)

    def get_launch_by_id(self, id):
        url = self.api_url + '/launch/%s?mode=verbose' % id
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
