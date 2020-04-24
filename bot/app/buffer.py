from buffpy import API
from buffpy.managers.profiles import Profiles

from spacelaunchnow import config

hashtags = '''\n
.
.
.⠀⠀
.⠀⠀
.⠀⠀
#SpaceLaunchNow #space #spacex #nasa #rocket #mars #aerospace #earth #solarsystem #iss #elonmusk
#moonlanding #spaceshuttle #spacewalk #esa #science #picoftheday #blueorigin #Florida #Falcon9
 #falconheavy #starship #ULA'''

class BufferAPI:
    def __init__(self, debug=None):
        if debug is None:
            self.DEBUG = config.DEBUG
        else:
            self.DEBUG = debug
        self.api = API(client_id=config.BUFFER_CLIENT_ID,
                       client_secret=config.BUFFER_SECRET_ID,
                       access_token=config.BUFFER_ACCESS_TOKEN)

    def send_to_all(self, message: str = None, image: str = None, link: str = None, now: bool = False, shorten: bool = True):
        profiles = Profiles(api=self.api).all()
        for profile in profiles:
            _message = message
            if profile['service'] == 'instagram' and image is None:
                continue
            if profile['service'] == 'twitter':
                if len(_message) > 280:
                    _message = (_message[:277] + '...')
            profile.updates.new(text=_message, photo=image, link=link, now=now, shorten=shorten)

    def send_to_instagram(self, message: str = None, image: str = None, now: bool = False):
        profile = Profiles(api=self.api).filter(service='instagram')[0]
        return profile.updates.new(text=message, photo=image, now=now)

    def send_to_facebook(self, message: str = None, image: str = None, link: str = None, now: bool = False):
        profile = Profiles(api=self.api).filter(service='facebook')[0]
        return profile.updates.new(text=message, link=link, photo=image, now=now)

    def send_to_twitter(self, message: str = None, image: str = None, link: str = None, now: bool = False):
        if len(message) > 280:
            message = (message[:277] + '...')
        profile = Profiles(api=self.api).filter(service='twitter')[0]
        return profile.updates.new(text=message, photo=image, link=link, now=now)
