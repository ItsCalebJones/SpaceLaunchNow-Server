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

    def __init__(self, user_auth_key, app_id=None, version='v1'):
        """
        Initializes the OneSignalSDK object.
        :param user_auth_key: This can be found by logging-in to http://onesignal.com and
        then clicking "API Keys" from the top right menu.
        :param app_id: You get an app_id once you are done creating an app using OneSignal's API,
        or you can pass app_id if there is already one.
        :param version: Version of the OneSignal API
        :return:
        """
        self.app_id = app_id
        self.user_auth_key = user_auth_key
        assert isinstance(version, basestring), 'version is not valid'
        self.api_url = BASE_URL + version

    def get_headers(self):
        """
        Gets the header to be used in subsequent calls.
        :return:
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Basic %s" % self.user_auth_key
        }
        return headers

    def get_players(self, app_auth_key, limit=300, offset=0):
        """
        Represents this endpoint;
        https://onesignal.com/api/v1/players?app_id=:app_id&limit=:limit&offset=:offset
        This endpoint requires Auth Key in header.
        :param app_auth_key: Each OneSignal App has a 'basic_auth_key'
        :param limit: Number of devices to return. Both max and default is 300.
        :param offset: Reset offset and default is 0.
        :return: Returns HTTP response object which contains a response that, per docs, looks like:
        .. Response::
            {
                "total_count": 3,
                "offset": 2,
                "limit": 2,
                "players": [{
                    "identifier": "ce777617da7f548fe7a9ab6febb56cf39fba6d382000c0395666288d961ee566",
                    "session_count": 1,
                    "language": "en",
                    "timezone": -28800,
                    "game_version": "1.0",
                    "device_os": "7.0.4",
                    "device_type": 0,
                    "device_model": "iPhone",
                    "ad_id": null,
                    "tags": {
                        "a": "1",
                        "foo": "bar"
                    },
                    "last_active": 1395096859,
                    "amount_spent": "0",
                    "created_at": 1395096859,
                    "invalid_identifier": false,
                    "badge_count": 0
                }]
            }
        """
        assert self.app_id, 'app_id must have a valid value'
        assert app_auth_key, 'app_auth_key must have a valid value'
        url = self.api_url + "/players?app_id=%s&limit=%s&offset=%s" % (self.app_id, limit, offset)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic %s' % app_auth_key
        }
        return send_request(url, method='GET', headers=headers)

    def get_player(self, player_id):
        """
        It takes data from this endpoint: https://onesignal.com/api/v1/players/:id
        :param player_id: ID of the player
        :return: Returns HTTP response object which contains a response that, per docs, looks like
        .. Response::
            {
                  "identifier":"ce777617da7f548fe7a9ab6febb56cf39fba6d382000c0395666288d961ee566",
                  "session_count":1,
                  "language":"en",
                  "timezone":-28800,
                  "game_version":"1.0",
                  "device_os":"7.0.4",
                  "device_type":0,
                  "device_model":"iPhone",
                  "ad_id":null,
                  "tags":{"a":"1","foo":"bar"},
                  "last_active":1395096859,
                  "amount_spent":"0",
                  "created_at":1395096859,
                  "invalid_identifier":false,
                  "badge_count": 0
            }
        : Example:
            client = OneSignalSdk(app_id='your_app_id',
                                 user_auth_key='rest_api_key')
            response = client.get_player("ce777617da7f548fe7a9ab6febb56cf39fba6d382000c0395666288d961ee566")
            response = response.json()
            # You can access response components like
            last_active = response['last_active']
            tags = response['tags]
        """
        assert player_id, 'player_id is not valid'
        url = self.api_url + "/players/" + player_id
        return send_request(url, method='GET')

    def create_player(self, device_type, app_id=None, **kwargs):
        """
        Sends a POST request to https://onesignal.com/api/v1/players to create a player.
        :param device_type: Required parameter to create a device. 0 = iOS, 1 = Android, 2 = Amazon,
            3 = WindowsPhone(MPNS), 4 = ChromeApp, 5 = ChromeWebsite, 6 = WindowsPhone(WNS), 7 = Safari,
            8 = Firefox
        :param app_id: OneSignal's app_id
        :param device_type: Required parameter to create a device. 0 = iOS, 1 = Android, 2 = Amazon,
        3 = WindowsPhone(MPNS), 4 = ChromeApp, 5 = ChromeWebsite, 6 = WindowsPhone(WNS), 7 = Safari,
        8 = Firefox
        :param kwargs: May add other parameters as given on
                    https://documentation.onesignal.com/docs/players-add-a-device
        :return: Returns HTTP response object which contains a response that, per docs, looks like:
        .. Response::
            {
                "success": true,
                "id": "ffffb794-ba37-11e3-8077-031d62f86ebf"
            }
        : Example:
            client = OneSignalSdk(app_id='your_app_id',
                                 user_auth_key='rest_api_key')
            response = client.create_player(1)
            response = response.json()
            # You can access response components like
            last_active = response['last_active']
            tags = response['tags]
        """
        app_id = app_id if app_id else self.app_id
        assert app_id, 'app_id must have a valid value'
        assert device_type in range(0, 9)
        url = self.api_url + "/players"
        kwargs['app_id'] = app_id
        kwargs['device_type'] = device_type
        data = json.dumps(kwargs)
        return send_request(url, method='POST', headers={
            'Content-Type': 'application/json'
        }, data=data)

    def edit_player(self, player_id, **kwargs):
        """
        Edits a player by sending a PUT request to https://onesignal.com/api/v1/players/:id
        :param player_id: Player's ID.
        :param kwargs: Represents other arguments this call can receiver per
        https://documentation.onesignal.com/docs/playersid-1
        :return: Returns HTTP response object which contains a response that, per docs, looks like:
        .. Response::
            {
                "success": true
            }
        """
        assert player_id, 'player is is not valid'
        url = self.api_url + "/players/" + player_id
        data = json.dumps(kwargs)
        return send_request(url, method='PUT', headers={
            'Content-Type': 'application/json'
        }, data=data)

    def player_on_session(self, player_id, **kwargs):
        """
        Call on new device session in your app
        :param player_id: Player's ID.
        :param kwargs: Other arguments as given here https://documentation.onesignal.com/docs/playersidon_session
        :return: Returns HTTP response object which contains a response that, per docs, looks like:
        .. Response::
            {
                "success": true
            }
        """
        assert player_id
        url = self.api_url + "/players/" + player_id + "/on_session"
        data = json.dumps(kwargs)
        return send_request(url, method='POST', headers={
            'Content-Type': 'application/json'
        }, data=data)

    def player_on_purchase(self, player_id, **kwargs):
        """
        Track a new purchase
        :param player_id: Player's ID
        :param kwargs: Take other arguments as given on https://documentation.onesignal.com/docs/on_purchase
        :return: Returns HTTP response object which contains a response that, per docs, looks like:
        .. Response::
            {
                "success": true
            }
        """
        assert player_id
        url = self.api_url + "/players/" + player_id + "/on_purchase"
        data = json.dumps(kwargs)
        return send_request(url, method='POST', headers={
            'Content-Type': 'application/json'
        }, data=data)

    def player_on_focus(self, player_id, **kwargs):
        """
        Increment the device's total session length.
        :param player_id: Player's ID
        :param kwargs: Take other arguments as given on https://documentation.onesignal.com/docs/playersidon_focus
        :return: Returns HTTP response object which contains a response that, per docs, looks like:
        .. Response::
            {
                "success": true
            }
        """
        assert player_id
        url = self.api_url + "/players/" + player_id + "/on_focus"
        data = json.dumps(kwargs)
        return send_request(url, method='POST', headers={
            'Content-Type': 'application/json'
        }, data=data)

    def create_app(self, app_name, **kwargs):
        """
        Creates a OneSignal app by sending a POST request to https://onesignal.com/api/v1/apps
        :param app_name: App's name
        :kwargs: Other arguments as given https://documentation.onesignal.com/docs/apps-create-an-app
            apns_env:	String
                    Either "sandbox" or "production"
            apns_p12:	String
                    Your apple push notification p12 certificate file, converted to
                    a string and Base64 encoded.
            apns_p12_password:	String
                    Password for the apns_p12 file
            gcm_key:	String
                    Your Google Push Messaging Auth Key
            chrome_key:	String
                    Your Google Push Messaging Auth Key for Chrome Push
            safari_apns_p12:	String
                    Your apple push notification p12 certificate file for Safari Push Notifications,
                    converted to a string and Base64 encoded.
            chrome_web_key:	String
                    A Google Push Messaging Auth Key For Chrome Web Push
            safari_apns_p12_password:	String
                    Password for safari_apns_p12 file
            site_name:	String
                    The URL to your website for Safari Web Push
            safari_site_origin:	String
                    The hostname to your website including http(s)://
            safari_icon_16_16:	String
                    A url for a 16x16 png for a safari notification icon
            safari_icon_32_32:	String
                    A url for a A 32x32 png for a safari notification icon
            safari_icon_64_64:	String
                    A url for a A 32x32 png for a safari notification icon
            safari_icon_128_128:	String
                    A url for a A 32x32 png for a safari notification icon
            safari_icon_256_256:	String
                    A url for a A 32x32 png for a safari notification icon
            chrome_web_origin:	String
                    The URL to your website for Chrome Web Push
            chrome_web_gcm_sender_id:	String
                    Your GCM Sender ID for Chrome Web Push
            chrome_web_default_notification_icon:	String
                    Your default notification icon for Chrome Web Push. Should be 80x80 pixels.
            chrome_web_sub_domain:	String
                    A subdomain of your choice in order to support Chrome Web Push on Non-HTTPs websites
        :return: Returns HTTP response object which contains a response that, per docs, looks like:
        .. Response:
            {
                id: "e4e87830-b954-11e3-811d-f3b376925f15",
                name: "Your app 1",
                players: 0,
                messagable_players: 0,
                updated_at: "2014-04-01T04:20:02.003Z",
                created_at: "2014-04-01T04:20:02.003Z",
                gcm_key: "a gcm push key",
                chrome_key: "A Chrome Web Push GCM key",
                chrome_web_origin: "Chrome Web Push Site URL",
                chrome_web_gcm_sender_id: "Chrome Web Push GCM Sender ID",
                chrome_web_default_notification_icon: "http://yoursite.com/chrome_notification_icon",
                chrome_web_sub_domain: "your_site_name",
                apns_env: "sandbox",
                apns_certificates: "Your apns certificate",
                safari_apns_cetificate: "Your Safari APNS certificate",
                safari_site_origin: "The homename for your website for Safari Push, including http or https",
                safari_push_id: "The certificate bundle ID for Safari Web Push",
                safari_icon_16_16: "http://onesignal.com/safari_packages/e4e87830-b954-11e3-811d-f3b376925f15/16x16.png",
                safari_icon_32_32: "http://onesignal.com/safari_packages/e4e87830-b954-11e3-811d-f3b376925f15/16x16@2.png",
                safari_icon_64_64: "http://onesignal.com/safari_packages/e4e87830-b954-11e3-811d-f3b376925f15/32x32@2x.png",
                safari_icon_128_128: "http://onesignal.com/safari_packages/e4e87830-b954-11e3-811d-f3b376925f15/128x128.png",
                safari_icon_256_256: "http://onesignal.com/safari_packages/e4e87830-b954-11e3-811d-f3b376925f15/128x128@2x.png",
                site_name: "The URL to your website for Web Push",
                basic_auth_key: "NGEwMGZmMjItY2NkNy0xMWUzLTk5ZDUtMDAwYzI5NDBlNjJj"
            }
        """
        url = self.api_url + "/apps"
        kwargs['name'] = app_name
        data = json.dumps(kwargs)
        response = send_request(url, method='POST', headers=self.get_headers(), data=data)
        if response.ok and not self.app_id:
            # If app creation was successful then update app id for this client
            resp = response.json()
            self.app_id = resp.get('id')
        return response

    def update_app(self, **kwargs):
        """
        Updates an app by sending a PUT to
            https://onesignal.com/api/v1/apps/:id
        :param kwargs: Other arguments as given on https://documentation.onesignal.com/docs/appsid-update-an-app
        :return: Returns HTTP response object which contains a response that, per docs, looks like
        .. Response::
            {
                id: "e4e87830-b954-11e3-811d-f3b376925f15",
                name: "Your app 1",
                players: 0,
                messagable_players: 0,
                updated_at: "2014-04-01T04:20:02.003Z",
                created_at: "2014-04-01T04:20:02.003Z",
                gcm_key: "a gcm push key",
                chrome_key: "A Chrome Web Push GCM key",
                chrome_web_origin: "Chrome Web Push Site URL",
                chrome_web_gcm_sender_id: "Chrome Web Push GCM Sender ID",
                chrome_web_default_notification_icon: "http://yoursite.com/chrome_notification_icon",
                chrome_web_sub_domain: "your_site_name",
                apns_env: "sandbox",
                apns_certificates: "Your apns certificate",
                safari_apns_cetificate: "Your Safari APNS certificate",
                safari_site_origin: "The homename for your website for Safari Push, including http or https",
                safari_push_id: "The certificate bundle ID for Safari Web Push",
                safari_icon_16_16: "http://onesignal.com/safari_packages/e4e87830-b954-11e3-811d-f3b376925f15/16x16.png",
                safari_icon_32_32: "http://onesignal.com/safari_packages/e4e87830-b954-11e3-811d-f3b376925f15/16x16@2.png",
                safari_icon_64_64: "http://onesignal.com/safari_packages/e4e87830-b954-11e3-811d-f3b376925f15/32x32@2x.png",
                safari_icon_128_128: "http://onesignal.com/safari_packages/e4e87830-b954-11e3-811d-f3b376925f15/128x128.png",
                safari_icon_256_256: "http://onesignal.com/safari_packages/e4e87830-b954-11e3-811d-f3b376925f15/128x128@2x.png",
                site_name: "The URL to your website for Web Push",
                basic_auth_key: "NGEwMGZmMjItY2NkNy0xMWUzLTk5ZDUtMDAwYzI5NDBlNjJj"
            }
        """
        assert self.app_id, 'app_id must have a valid value'
        url = self.api_url + "/apps/" + self.app_id
        data = json.dumps(kwargs)
        return send_request(url, method='PUT', headers=self.get_headers(), data=data)

    def get_apps(self):
        """
        GET Apps by sending a GET to
            https://onesignal.com/api/v1/apps
        :return: Returns HTTP response object which contains a response that, per docs, looks like
        .. Response::
            [{
                {
                    id: "92911750-242d-4260-9e00-9d9034f139ce",
                    name: "Your app 1",
                    players: 150,
                    messagable_players: 143,
                    updated_at: "2014-04-01T04:20:02.003Z",
                    created_at: "2014-04-01T04:20:02.003Z",
                    gcm_key: "a gcm push key",
                    chrome_key: "A Chrome Web Push GCM key",
                    chrome_web_origin: "Chrome Web Push Site URL",
                    chrome_web_gcm_sender_id: "Chrome Web Push GCM Sender ID",
                    chrome_web_default_notification_icon: "http://yoursite.com/chrome_notification_icon",
                    chrome_web_sub_domain: "your_site_name",
                    apns_env: "sandbox",
                    apns_certificates: "Your apns certificate",
                    safari_apns_cetificate: "Your Safari APNS certificate",
                    safari_site_origin: "The homename for your website for Safari Push, including http or https",
                    safari_push_id: "The certificate bundle ID for Safari Web Push",
                    safari_icon_16_16: "http://onesignal.com/safari_packages/92911750-242d-4260-9e00-9d9034f139ce/16x16.png",
                    safari_icon_32_32: "http://onesignal.com/safari_packages/92911750-242d-4260-9e00-9d9034f139ce/16x16@2.png",
                    safari_icon_64_64: "http://onesignal.com/safari_packages/92911750-242d-4260-9e00-9d9034f139ce/32x32@2x.png",
                    safari_icon_128_128: "http://onesignal.com/safari_packages/92911750-242d-4260-9e00-9d9034f139ce/128x128.png",
                    safari_icon_256_256: "http://onesignal.com/safari_packages/92911750-242d-4260-9e00-9d9034f139ce/128x128@2x.png",
                    site_name: "The URL to your website for Web Push",
                    basic_auth_key: "NGEwMGZmMjItY2NkNy0xMWUzLTk5ZDUtMDAwYzI5NDBlNjJj"
                }
            }]
        """
        url = self.api_url + "/apps"
        return send_request(url, method='GET', headers=self.get_headers())

    def get_app(self, app_id=None):
        """
        Gets an app by sending a GET to https://onesignal.com/api/v1/apps/:id
        :param app_id: App's ID
        :return: Returns HTTP response object which contains a response that, per docs, looks like:
        .. Response::
            {
                  id: "92911750-242d-4260-9e00-9d9034f139ce",
                  name: "Your app 1",
                  players: 150,
                  messagable_players: 143,
                  updated_at: "2014-04-01T04:20:02.003Z",
                  created_at: "2014-04-01T04:20:02.003Z",
                  gcm_key: "a gcm push key",
                  chrome_key: "A Chrome Web Push GCM key",
                  chrome_web_origin: "Chrome Web Push Site URL",
                  chrome_web_gcm_sender_id: "Chrome Web Push GCM Sender ID",
                  chrome_web_default_notification_icon: "http://yoursite.com/chrome_notification_icon",
                  chrome_web_sub_domain:"your_site_name",
                  apns_env: "sandbox",
                  apns_certificates: "Your apns certificate",
                  safari_apns_cetificate: "Your Safari APNS certificate",
                  safari_site_origin: "The homename for your website for Safari Push, including http or https",
                  safari_push_id: "The certificate bundle ID for Safari Web Push",
                  safari_icon_16_16: "http://onesignal.com/safari_packages/92911750-242d-4260-9e00-9d9034f139ce/16x16.png",
                  safari_icon_32_32: "http://onesignal.com/safari_packages/92911750-242d-4260-9e00-9d9034f139ce/16x16@2.png",
                  safari_icon_64_64: "http://onesignal.com/safari_packages/92911750-242d-4260-9e00-9d9034f139ce/32x32@2x.png",
                  safari_icon_128_128: "http://onesignal.com/safari_packages/92911750-242d-4260-9e00-9d9034f139ce/128x128.png",
                  safari_icon_256_256: "http://onesignal.com/safari_packages/92911750-242d-4260-9e00-9d9034f139ce/128x128@2x.png",
                  site_name: "The URL to your website for Web Push",
                  basic_auth_key: "NGEwMGZmMjItY2NkNy0xMWUzLTk5ZDUtMDAwYzI5NDBlNjJj"
            }
        """
        app_id = app_id if app_id else self.app_id
        url = self.api_url + "/apps/" + app_id
        return send_request(url, method='GET', headers=self.get_headers())

    def export_players_to_csv(self, app_auth_key, app_id=None):
        """
        Sends a GET to https://onesignal.com/api/v1/players/csv_export?app_id=:app_id and in
        return it sends a URL through which CSV file can be downloaded.
        :param app_auth_key: App auth key
        :param app_id: App's ID.
        :return: Returns HTTP response object which contains a response,per their docs, that looks like:
        .. Response::
            {
                "csv_file_url":
                "https://onesignal.com/csv_exports/b2f7f966-d8cc-11e4-bed1-df8f05be55ba/users_184948440ec0e334728e87228011ff41_2015-11-10.csv"
            }
        """
        app_id = app_id if app_id else self.app_id
        assert app_id, 'app_id can not be empty'
        url = self.api_url + "/players/csv_export?app_id=" + app_id
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic %s' % app_auth_key
        }
        return send_request(url, headers=headers, method='POST')

    def create_notification(self, contents=None, heading='', url='',
                            included_segments=('All',), app_id=None, player_ids=None, **kwargs):
        """
        Creates a notification by sending a notification to https://onesignal.com/api/v1/notifications
        :param heading: push notification heading / title
        :param url: target url for push notification. User will be redirected to this url on clicking
        push notification
        :param app_id: App's ID
        :param contents: Contents of the message
        :param player_ids: list of player_ids to whom we specifically want to send notifications
        :param included_segments: segments to be included to send push notification
        :param kwargs: There can be more arguments as given on
        https://documentation.onesignal.com/docs/notifications-create-notification
        :return: Returns a HTTP response object which, per docs, will contain response like:
        .. Response::
            {
                  "id": "458dcec4-cf53-11e3-add2-000c2940e62c",
                  "recipients": 5
            }
        """
        app_id = app_id if app_id else self.app_id
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

        if player_ids and isinstance(player_ids, (list, tuple)):
            data['include_player_ids'] = player_ids
        elif isinstance(included_segments, (list, tuple)) and len(included_segments):
            data['included_segments'] = included_segments

        if kwargs:
            data.update(kwargs)

        api_url = self.api_url + "/notifications"
        data = json.dumps(data)
        logger.info('URL: %s' % api_url)
        logger.info('DATA: %s' % data)
        return send_request(api_url, method='POST', headers=self.get_headers(), data=data)

    def get_notification(self, app_id, notification_id, app_auth_key):
        """
        Gets a notification by sending a GET to https://onesignal.com/api/v1/notifications/:id?app_id=:app_id
        :param app_id: App's ID
        :param notification_id: Notification ID that you want to get.
        :param app_auth_key: App's auth key
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

        assert app_id and notification_id and app_auth_key
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic %s' % app_auth_key
        }
        url = self.api_url + ('/notifications/%s?app_id=%s' % (notification_id, app_id))
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
