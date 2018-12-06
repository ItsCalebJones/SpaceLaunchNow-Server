import datetime
import pytz
import requests
import tempfile
import logging


try:
    from urllib import quote  # Python 2.X
except ImportError:
    from urllib.parse import quote  # Python 3+

from api.models import *
from api.utils.utilities import get_mission_type, get_agency_type, get_launch_status
from bot.models import *
from configurations.models import *
from django.core import files

logger = logging.getLogger('bot.digest')


def launch_status_json_to_model(data):
    id = data['id']
    name = data['name']
    launch_status, created = LaunchStatus.objects.get_or_create(id=id, name=name)
    return launch_status


def agency_type_json_to_model(data):
    id = data['id']
    name = data['name']
    launch_status, created = AgencyType.objects.get_or_create(id=id, name=name)
    return launch_status


def mission_type_json_to_model(data):
    id = data['id']
    name = data['name']
    launch_status, created = MissionType.objects.get_or_create(id=id, name=name)
    return launch_status


def launch_json_to_model(data):
    id = data['id']
    name = data['name']
    status = data['status']
    inhold = data['inhold']
    net = data['net']
    window_end = data['windowend']
    window_start = data['windowstart']
    vid_urls = data['vidURLs']
    info_urls = data['infoURLs']
    probability = data['probability']
    holdreason = data['holdreason']
    failreason = data['failreason']
    hashtag = data['hashtag']
    tbdtime = data['tbdtime']
    tbddate = data['tbddate']

    launch, created = Launch.objects.get_or_create(launch_library_id=id)
    launch.name = name

    if created:
        logger.info("Created - %s (%s)" % (launch.name, launch.id))

    try:
        launch.status = LaunchStatus.objects.get(id=status)
    except ObjectDoesNotExist:
        launch.status = LaunchStatus.objects.get(id=2)
        logger.error("Launch did not have a status.")
    launch.inhold = inhold
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
    launch.mission = get_mission(launch, data)
    launch.rocket = get_rocket(launch, data)
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
        if created:
            location.name = data['location']['name']
            location.country_code = data['location']['countryCode']
        location.save()
        if data['location']['pads'] is not None and len(data['location']['pads']) > 0:
                pad, created = Pad.objects.get_or_create(id=data['location']['pads'][0]['id'], location=location)
                if created:
                    pad.name = data['location']['pads'][0]['name'].split(',', 1)[0]
                pad.map_url = data['location']['pads'][0]['mapURL']
                pad.wiki_url = data['location']['pads'][0]['wikiURL']
                pad.latitude = data['location']['pads'][0]['latitude']
                pad.longitude = data['location']['pads'][0]['longitude']
                if data['location']['pads'][0]['agencies'] and len(data['location']['pads'][0]['agencies']) > 0:
                    pad.agency_id = data['location']['pads'][0]['agencies'][0]['id']
                launch.pad = pad
                pad.save()
        return location


def get_rocket(launch, data):
    if 'rocket' in data and data['rocket'] is not None:
        launcher_config, created = LauncherConfig.objects.get_or_create(id=data['rocket']['id'])
        if created:
            launcher_config.name = data['rocket']['name']
            launcher_config.family_name = data['rocket']['familyname']
            launcher_config.configuration = data['rocket']['configuration']
            launcher_config.launch_agency = get_lsp(launch, data)
        launcher_config.save()
        if 'placeholder' not in data['rocket']['imageURL'] and created:
            download_launcher_image(launcher_config)
        rocket, created = Rocket.objects.get_or_create(launch__id=launch.id, configuration=launcher_config)
    return rocket


def get_mission(launch, data):
    if data['missions'] is not None and len(data['missions']) > 0:
        mission, created = Mission.objects.get_or_create(id=data['missions'][0]['id'])
        mission.name = data['missions'][0]['name']
        mission.type = data['missions'][0]['type']
        mission.type_name = get_mission_type(data['missions'][0]['type'])
        if data['missions'][0]['type'] != 0:
            mission_type, created = MissionType.objects.get_or_create(id=data['missions'][0]['type'])
            if created:
                mission_type.name = "Unknown"
            mission.mission_type = mission_type
        mission.description = data['missions'][0]['description']
        mission.save()
        # if data['missions'][0]['payloads'] is not None and len(data['missions'][0]['payloads']) > 0:
        #     for payload_data in data['missions'][0]['payloads']:
        #         payload, created = Payload.objects.get_or_create(id=payload_data['id'])
        #         payload.name = payload_data['name']
        #         # payload.type = payload_data['type']
        #         # payload.type_name = get_mission_type(payload_data['type'])
        #         # payload.description = payload_data['description']
        #         payload.mission.add(mission)
        return mission


def get_lsp(launch, data):
    if 'lsp' in data and data['lsp'] is not None:
        lsp, created = Agency.objects.get_or_create(id=data['lsp']['id'])
        lsp.name = data['lsp']['name']
        lsp.country_code = data['lsp']['countryCode']
        lsp.abbrev = data['lsp']['abbrev']
        if data['lsp']['type'] != 0:
            agency_type = AgencyType.objects.get(id=data['lsp']['type'])
            lsp.agency_type = agency_type
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
    clean_name = quote(quote(launcher.name.encode('utf8')), '')
    clean_name = "%s_nation_%s" % (clean_name.lower(), datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    name = "%s%s" % (str(clean_name), file_extension)

    lf = tempfile.NamedTemporaryFile()

    for block in request.iter_content(1024 * 8):
        if not block:
            break
        lf.write(block)

    image_file = LauncherConfig.objects.get(id=launcher.id).image_url
    image_file.save(name, files.File(lf))
