import requests
from simplejson import JSONDecodeError

url = "http://calebjones.me/app/orbiter"
headers = {
    "Content-Type": "application/json"
}


method = getattr(requests, 'get')
response = method(url=url, data=None, headers=headers)
try:
    data = response.json()
except JSONDecodeError as e:

print data

for launch in data:
    print launch


