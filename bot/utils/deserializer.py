import datetime
import pytz
import requests
import tempfile

from api.models import *
from api.utils.utilities import get_mission_type, get_agency_type, get_launch_status
from bot.models import *
from django.core import files


def launch_json_to_model(data):
    id = data['id']
    name = data['name']
    status = data['status']
    if status < 1 or status > 7:
        print id
    status_name = get_launch_status(data['status'])
    netstamp = data['netstamp']
    wsstamp = data['wsstamp']
    westamp = data['westamp']
    inhold = data['inhold']
    net = data['net']
    window_end = data['windowend']
    window_start = data['windowstart']
    vid_urls = data['vidURLs']
    info_urls = data['infoURLs']
    isonet = data['isonet']
    isostart = data['isostart']
    isoend = data['isoend']
    probability = data['probability']
    holdreason = data['holdreason']
    failreason = data['failreason']
    hashtag = data['hashtag']
    tbdtime = data['tbdtime']
    tbddate = data['tbddate']

    launch, created = Launch.objects.get_or_create(id=id)
    launch.name = name
    launch.status = status
    launch.status_name = status_name
    launch.netstamp = netstamp
    launch.wsstamp = wsstamp
    launch.westamp = westamp
    launch.inhold = inhold
    launch.isonet = isonet
    launch.isostart = isostart
    launch.isoend = isoend
    launch.probability = probability
    launch.holdreason = holdreason
    launch.failreason = failreason
    launch.hashtag = hashtag
    launch.tbddate = tbddate
    launch.tbdtime = tbdtime
    launch.net = datetime.datetime.strptime(net, '%B %d, %Y %H:%M:%S %Z').replace(tzinfo=pytz.utc)
    launch.window_end = datetime.datetime.strptime(window_end, '%B %d, %Y %H:%M:%S %Z').replace(tzinfo=pytz.utc)
    launch.window_start = datetime.datetime.strptime(window_start, '%B %d, %Y %H:%M:%S %Z').replace(tzinfo=pytz.utc)

    launch.vid_urls.all().delete()
    for url in vid_urls:
        VidURLs.objects.create(vid_url=url, launch=launch)
    launch.info_urls.all().delete()
    for url in info_urls:
        InfoURLs.objects.create(info_url=url, launch=launch)
    launch.location = get_location(launch, data)
    launch.launcher = get_rocket(launch, data)
    launch.mission = get_mission(launch, data)
    launch.lsp = get_lsp(launch, data)
    check_notification(launch)
    launch.save()
    return launch


def check_notification(launch):
    current = datetime.datetime.now(tz=utc)
    if launch.net >= current:
        try:
            if Notification.objects.get(launch=launch) is None:
                Notification.objects.get_or_create(launch=launch)
        except Notification.DoesNotExist:
            Notification.objects.get_or_create(launch=launch)


def get_location(launch, data):
    if 'location' in data and data['location'] is not None:
        location, created = Location.objects.get_or_create(id=data['location']['id'])
        location.name = data['location']['name']
        location.country_code = data['location']['countryCode']
        location.save()
        if data['location']['pads'] is not None and len(data['location']['pads']) > 0:
                pad, created = Pad.objects.get_or_create(id=data['location']['pads'][0]['id'], location=location)
                pad.name = data['location']['pads'][0]['name']
                pad.map_url = data['location']['pads'][0]['mapURL']
                pad.wiki_url = data['location']['pads'][0]['wikiURL']
                pad.latitude = data['location']['pads'][0]['latitude']
                pad.longitude = data['location']['pads'][0]['longitude']
                launch.pad = pad
                pad.save()
        return location


def get_rocket(launch, data):
    if 'rocket' in data and data['rocket'] is not None:
        rocket, created = Launcher.objects.get_or_create(id=data['rocket']['id'])
        if created:
            rocket.name = data['rocket']['name']
            rocket.family_name = data['rocket']['familyname']
            rocket.configuration = data['rocket']['configuration']
        rocket.launch.add(launch)
        rocket.save()
        if 'placeholder' not in data['rocket']['imageURL'] and created:
            download_launcher_image(rocket)
    return rocket


def get_mission(launch, data):
    if data['missions'] is not None and len(data['missions']) > 0:
        mission, created = Mission.objects.get_or_create(id=data['missions'][0]['id'])
        mission.name = data['missions'][0]['name']
        mission.type = data['missions'][0]['type']
        mission.type_name = get_mission_type(data['missions'][0]['type'])
        mission.description = data['missions'][0]['description']
        mission.save()
        return mission


def get_lsp(launch, data):
    if 'lsp' in data and data['lsp'] is not None:
        lsp, created = Agency.objects.get_or_create(id=data['lsp']['id'])
        lsp.name = data['lsp']['name']
        lsp.country_code = data['lsp']['countryCode']
        lsp.abbrev = data['lsp']['abbrev']
        lsp.type = get_agency_type(data['lsp']['type'])
        if len(data['lsp']['infoURLs']) > 0:
            lsp.info_url = data['lsp']['infoURLs'][0]
        lsp.wiki_url = data['lsp']['wikiURL']
        lsp.save()
        return lsp


def download_launcher_image(launcher):
    result = requests.get("http://launchlibrary.net/1.3/rocket/" + str(launcher.id))
    webrocket = result.json()['rockets'][0]

    request = requests.get(webrocket['imageURL'], stream=True)
    filename = webrocket['imageURL'].split('/')[-1]
    filename, file_extension = os.path.splitext(filename)
    clean_name = urllib.quote(urllib.quote(launcher.name.encode('utf8')), '')
    clean_name = "%s_nation_%s" % (clean_name.lower(), datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    name = "%s%s" % (str(clean_name), file_extension)

    lf = tempfile.NamedTemporaryFile()

    for block in request.iter_content(1024 * 8):
        if not block:
            break
        lf.write(block)

    image_file = Launcher.objects.get(id=launcher.id).image_url
    image_file.save(name, files.File(lf))
