# coding=utf-8
import codecs
import io
import json
import os
import textwrap
import urllib

from instagram_private_api import Client, ClientCookieExpiredError, ClientLoginError
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from bot.utils.util import custom_strftime
from spacelaunchnow import config

settings_file = "instagram.cache"

username = config.INSTAGRAM_USERNAME
password = config.INSTAGRAM_PASSWORD


def to_json(python_object):
    if isinstance(python_object, bytes):
        return {
            "__class__": "bytes",
            "__value__": codecs.encode(python_object, "base64").decode(),
        }
    raise TypeError(repr(python_object) + " is not JSON serializable")


def from_json(json_object):
    if "__class__" in json_object and json_object["__class__"] == "bytes":
        return codecs.decode(json_object["__value__"].encode(), "base64")
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
                seed="{pw!s}.{usr!s}.{ts!s}".format(
                    **{"pw": username, "usr": password, "ts": ts_seed}
                )
            )

            device_id = Client.generate_deviceid(
                seed="{usr!s}.{ts!s}.{pw!s}".format(
                    **{"pw": password, "usr": username, "ts": ts_seed}
                )
            )

            # start afresh without existing auth
            try:
                self.instagram = Client(
                    username,
                    password,
                    auto_patch=True,
                    drop_incompat_keys=False,
                    guid=uuid,
                    device_id=device_id,
                )

            except ClientLoginError:
                print("Login Error. Please check your username and password.")

            # stuff that you should cache
            cached_auth = self.instagram.settings
            with open(settings_file, "w") as outfile:
                json.dump(cached_auth, outfile, default=to_json)

        else:
            try:
                # remove previous app version specific info so that we
                # can test the new sig key whenever there's an update
                for k in [
                    "app_version",
                    "signature_key",
                    "key_version",
                    "ig_capabilities",
                ]:
                    cached_auth.pop(k, None)
                self.instagram = Client(
                    username,
                    password,
                    auto_patch=True,
                    drop_incompat_keys=False,
                    settings=cached_auth,
                )

            except ClientCookieExpiredError:
                print("Cookie Expired. Please discard cached auth and login again.")

    def update_profile(self, message, url="https://spacelaunchnow.me"):
        return self.instagram.edit_profile(
            external_url=url,
            first_name="Space Launch Now",
            biography=message,
            gender="3",
            email=config.INSTAGRAM_EMAIL,
            phone_number="",
        )

    def create_post(self, launch, time_remaining="one hour"):
        MAX_W = 1080
        MAX_H = 1080
        size = (MAX_W, MAX_H)

        if launch.img_url:
            # Download the Image
            fd = urllib.urlopen(launch.img_url)
            image_file = io.BytesIO(fd.read())
            im = Image.open(image_file)
        else:
            im = Image.open("static/img/header.jpg")

        width, height = im.size

        # Crop the Image
        left = (width - MAX_W) / 2
        top = (height - MAX_H) / 2
        right = (width + MAX_W) / 2
        bottom = (height + MAX_H) / 2
        im = im.crop((left, top, right, bottom))

        # Create Text
        text = Image.new("RGBA", size)
        text_shadow = Image.new("RGBA", size)
        shadowcolor = (0, 0, 0, 128)

        # Create Header Text
        header = launch.name
        font = ImageFont.truetype("static/font/RobotoCondensed-Bold.ttf", 120)
        para = textwrap.wrap(header, width=20)
        draw = ImageDraw.Draw(text)
        draw_shadow = ImageDraw.Draw(text_shadow)
        current_h, pad = 50, 10

        for line in para:
            w, h = draw.textsize(line, font=font)
            x = (MAX_W - w) / 2
            y = current_h
            draw_shadow.text((x + 5, y), line, font=font, fill=shadowcolor)
            draw_shadow.text((x, y + 5), line, font=font, fill=shadowcolor)

            draw.text((x, y), line, font=font)
            current_h += h + pad

        # Create Body Text
        message = u"""
        Mission: %s
        Location: %s
        Date: %s
        """ % (
            launch.mission.type_name,
            launch.pad.location.name,
            custom_strftime("%B {S} at %I:%M %p %Z", launch.net),
        )
        font = ImageFont.truetype("static/font/RobotoCondensed-Bold.ttf", 60)
        w, h = draw.textsize(message, font=font)
        x = (MAX_W - w) / 2
        y = (MAX_H - h) / 2
        draw_shadow.text((x + 5, y), message, font=font, fill=shadowcolor)
        draw_shadow.text((x, y + 5), message, font=font, fill=shadowcolor)

        draw.text((x, y), message, font=font)

        # Create Footer
        font = ImageFont.truetype("static/font/RobotoCondensed-Bold.ttf", 100)
        footer = "Launching in %s!" % time_remaining
        para = textwrap.wrap(footer, width=100)
        draw = ImageDraw.Draw(text)
        current_h, pad = 50, 10

        for line in para:
            w, h = draw.textsize(line, font=font)
            x = (MAX_W - w) / 2
            y = MAX_H - 200
            draw_shadow.text((x + 5, y), line, font=font, fill=shadowcolor)
            draw_shadow.text((x, y + 5), line, font=font, fill=shadowcolor)

            draw.text((x, y), line, font=font)
            current_h += h + pad
        text_shadow = text_shadow.filter(ImageFilter.GaussianBlur(radius=5))
        text_shadow.paste(text, (0, 0), text)
        im = im.filter(ImageFilter.GaussianBlur(radius=5))
        im.paste(text_shadow, (0, 0), text_shadow)
        im = im.convert("RGB")
        im.save("temp.jpg", "JPEG")
        in_file = open("temp.jpg", "rb")
        results = self.instagram.post_photo(
            in_file.read(), size=size, caption=launch.name
        )
        in_file.close()
        os.remove("temp.jpg")
        assert "ok" in results.get("status")
