from spacelaunchnow import config


class EventTwitterHandler:
    def __init__(self, debug=None):
        if debug is None:
            self.DEBUG = config.DEBUG
        else:
            self.DEBUG = debug

    def send_ten_minute_tweet(self, event):
        pass

    def send_webcast_tweet(self, event):
        pass
