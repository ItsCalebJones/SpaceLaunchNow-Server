import os
import codecs
import json

from instagram_private_api import Client, ClientCompatPatch, ClientLoginError, ClientCookieExpiredError

from spacelaunchnow import config

settings_file = 'instagram.cache'

username = config.INSTAGRAM_USERNAME
password = config.INSTAGRAM_PASSWORD


def to_json(python_object):
    if isinstance(python_object, bytes):
        return {'__class__': 'bytes',
                '__value__': codecs.encode(python_object, 'base64').decode()}
    raise TypeError(repr(python_object) + ' is not JSON serializable')


def from_json(json_object):
    if '__class__' in json_object and json_object['__class__'] == 'bytes':
        return codecs.decode(json_object['__value__'].encode(), 'base64')
    return json_object


class InstagramBot:
    def __init__(self, debug=None):
        if debug is None:
            self.DEBUG = False
        else:
            self.DEBUG = debug
        cached_auth = None
        if os.path.isfile(settings_file):
            with open(settings_file) as file_data:
                cached_auth = json.load(file_data, object_hook=from_json)

        if not cached_auth:

            ts_seed = str(int(os.path.getmtime(__file__)))
            # Example of how to generate a uuid.
            # You can generate a fixed uuid if you use a fixed value seed
            uuid = Client.generate_uuid(
                seed='{pw!s}.{usr!s}.{ts!s}'.format(**{'pw': username, 'usr': password, 'ts': ts_seed}))

            device_id = Client.generate_deviceid(
                seed='{usr!s}.{ts!s}.{pw!s}'.format(**{'pw': password, 'usr': username, 'ts': ts_seed}))

            # start afresh without existing auth
            try:
                self.instagram = Client(
                    username, password,
                    auto_patch=True, drop_incompat_keys=False,
                    guid=uuid, device_id=device_id, )

            except ClientLoginError:
                print('Login Error. Please check your username and password.')

            # stuff that you should cache
            cached_auth = self.instagram.settings
            with open(settings_file, 'w') as outfile:
                json.dump(cached_auth, outfile, default=to_json)

        else:
            try:
                # remove previous app version specific info so that we
                # can test the new sig key whenever there's an update
                for k in ['app_version', 'signature_key', 'key_version', 'ig_capabilities']:
                    cached_auth.pop(k, None)
                self.instagram = Client(
                    username, password,
                    auto_patch=True, drop_incompat_keys=False,
                    settings=cached_auth)

            except ClientCookieExpiredError:
                print('Cookie Expired. Please discard cached auth and login again.')

    def update_profile(self, message):
        self.instagram.edit_profile(external_url='https://spacelaunchnow.me/',
                                    first_name='Space Launch Now',
                                    biography=message,
                                    gender='3',
                                    email='ca.jones9119+spacelaunchnow@gmail.com',
                                    phone_number=None)
