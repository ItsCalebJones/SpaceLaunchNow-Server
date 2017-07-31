import requests
import simplejson as json
import re
import api.utils.deserializer

headers = {
    "Content-Type": "application/json"
}


class importer:
    def __init__(self):
        pass

    def validate_text(self, text):
        pattern = r'\\'
        regex = re.compile(pattern, re.IGNORECASE)
        return re.sub(regex, '', text)

    def parse_json(self, text):
        text = self.validate_text(text)
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            print e.message

    def get_orbiter(self):
        url = "http://calebjones.me/app/orbiter"
        return self.get_response_from_url(url)

    def get_launchers(self):
        url = "http://calebjones.me/app/launchers"
        return self.get_response_from_url(url)

    def get_launcher_details(self):
        url = "http://calebjones.me/app/vehicle"
        return self.get_response_from_url(url)

    def get_response_from_url(self, url):
        method = getattr(requests, 'get')
        return method(url=url, data=None, headers=headers)

    def orbiter(self):
        return self.parse_json(self.get_orbiter().text)

    def launcher(self):
        return self.parse_json(self.get_launchers().text)

    def launcher_details(self):
        return self.parse_json(self.get_launcher_details().text)


def main():
    orbiters = importer().orbiter()
    for item in orbiters['items']:
        api.utils.deserializer.orbiter_json_to_model(item)

    launchers = importer().launcher()
    for item in launchers['items']:
        api.utils.deserializer.launcher_json_to_model(item)

    launcher_details = importer().launcher_details()
    for item in launcher_details['vehicles']:
        api.utils.deserializer.launch_detail_to_model(item)

if __name__ == "__main__":
    main()
