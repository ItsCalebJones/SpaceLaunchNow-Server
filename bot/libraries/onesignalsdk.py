"""
This module contains code that implements API calls for OneSignal Restful API. Some important concepts:
App: Represents a single App across all platforms.
Players (aka devices or users): Each OneSignal app represent many users.
Notification: A notification can be sent to individuals, segments and users.
Two type of API keys are used and it's important to distinguish them. As per their docs available at
https://documentation.onesignal.com/docs/server-api-overview:
---------------------------------------------------------------------------------------------------
Some API methods require User or App authentication REST API Keys. They are:
1. OneSignal App creation or modification - Requires your OneSignal 'User REST API Key'.
2. Notification Creation - Requires your OneSignal 'App REST API Key' when specifying
targets using "tags" or "included_segments". Otherwise no token is required.
Also note:
The 'User REST API Key' is visible on the "Account Management" page under the "API Keys" tab.
The 'App REST API Key' is under the "Application Settings" page under the "API Keys" tab.
---------------------------------------------------------------------------------------------------
"""
import re
import json

import logging
import requests

# Get an instance of a logger
logger = logging.getLogger('bot')

BASE_URL = 'https://onesignal.com/api/'


class OneSignalSdk(object):

    def __init__(self, rest_auth_key, app_id=None, version='v1'):
        """
        Initializes the OneSignalSDK object.
        :param rest_auth_key: This can be found by logging-in to http://onesignal.com and
        then clicking "API Keys" from the top right menu.
        :param app_id: You get an app_id once you are done creating an app using OneSignal's API,
        or you can pass app_id if there is already one.
        :param version: Version of the OneSignal API
        :return:
        """
        self.app_id = app_id
        self.rest_auth_key = rest_auth_key
        assert isinstance(version, basestring), 'version is not valid'
        self.api_url = BASE_URL + version

    def get_headers(self):
        """
        Gets the header to be used in subsequent calls.
        :return:
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Basic %s" % self.rest_auth_key
        }
        return headers

    def create_notification(self, contents=None, heading='', url='', included_segments=None, excluded_segments=None, **kwargs):

        """
        Creates a notification by sending a notification to https://onesignal.com/api/v1/notifications
        :param heading: push notification heading / title
        :param url: target url for push notification. User will be redirected to this url on clicking
        push notification
        :param app_id: App's ID
        :param contents: Contents of the message
        :param player_ids: list of player_ids to whom we specifically want to send notifications
        :param included_segments: segments to be included to send push notification
        :param included_segments: segments to be excluded to send push notification
        :param kwargs: There can be more arguments as given on
        https://documentation.onesignal.com/docs/notifications-create-notification
        :return: Returns a HTTP response object which, per docs, will contain response like:
        .. Response::
            {
                  "id": "458dcec4-cf53-11e3-add2-000c2940e62c",
                  "recipients": 5
            }
        """
        app_id = self.app_id
        assert app_id
        data = {
            "app_id": app_id
        }
        if isinstance(contents, dict):
            data['contents'] = contents
        elif contents:
            data['contents'] = {'en': contents}
        if url and is_valid_url(url):
            data['url'] = url
        if isinstance(heading, dict):
            data['headings'] = heading
        else:
            data['headings'] = {'en': heading}

        if isinstance(included_segments, (list, tuple)) and len(included_segments):
            data['included_segments'] = included_segments
        if isinstance(excluded_segments, (list, tuple)) and len(excluded_segments):
            data['excluded_segments'] = excluded_segments

        if kwargs:
            data.update(kwargs)

        api_url = self.api_url + "/notifications"
        data = json.dumps(data)
        logger.info('URL: %s' % api_url)
        logger.info('DATA: %s' % data)
        return send_request(api_url, method='POST', headers=self.get_headers(), data=data)

    def get_notification(self, notification_id):
        """
        Gets a notification by sending a GET to https://onesignal.com/api/v1/notifications/:id?app_id=:app_id
        :param notification_id: Notification ID that you want to get.
        :return: Returns a HTTP response object which, per docs, will contain response like:
        .. Response::
            {
                "id": "481a2734-6b7d-11e4-a6ea-4b53294fa671",
                "successful": 15,
                "failed": 1,
                "converted": 3,
                "remaining": 0,
                "queued_at": 1415914655,
                "send_after": 1415914655,
                "data": {
                    "foo": "bar",
                    "your": "custom metadata"
                },
                "canceled": false,
                "headings": {
                    "en": "English and default langauge heading",
                    "es": "Spanish language heading"
                },
                "contents": {
                    "en": "English language content",
                    "es": "Hola"
                }
            }
        """

        assert self.app_id and notification_id and self.rest_auth_key
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic %s' % self.rest_auth_key
        }
        url = self.api_url + ('/notifications/%s?app_id=%s' % (notification_id, self.app_id))
        return send_request(url, method='GET', headers=headers)

    def delete_notification(self, notification_id):
        """
        Deletes a notification by sending a DELETE to https://onesignal.com/api/v1/notifications/:id?app_id=:app_id
        :param notification_id:  Notification ID that you want to delete
        :return: Returns a HTTP response object which, per docs, will contain response like:
        .. Response::
            {
                "success": "true"
            }
        """
        assert notification_id
        url = self.api_url + ('/notifications/%s?app_id=%s' % (notification_id, self.app_id))
        return send_request(url, method='DELETE', headers=self.get_headers())


def is_valid_url(url):
    """
    Reference: https://github.com/django/django-old/blob/1.3.X/django/core/validators.py#L42
    """
    regex = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url is not None and regex.search(url)


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
