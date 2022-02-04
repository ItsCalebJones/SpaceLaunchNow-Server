import datetime
import pytz
import requests
import tempfile
import logging

from goose3 import Goose

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
    launch_status, created = LaunchStatus.objects.get_or_create(id=id, legacy_name=name)
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


def rocket_json_to_model(data):
    try:
        launcher_config = LauncherConfig.objects.get(launch_library_id=data['id'])
    except LauncherConfig.DoesNotExist:
        launcher_config = LauncherConfig(launch_library_id=data['id'])
        launcher_config.name = data['name']
        launcher_config.full_name = data['name']
        launcher_config.family_name = data['family']['name']
        launcher_config.configuration = data['configuration']
        if 'placeholder' not in data['imageURL'] and launcher_config.image_url is None:
            download_launcher_image(launcher_config)
    launcher_config.save()


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
    launch_service_provider = get_lsp(data)
    pad = get_location(data)

    launch, created = Launch.objects.get_or_create(launch_library_id=id)
    launch.name = name
    launch.launch_library = True

    if created:
        logger.info("Created - %s (%s)" % (launch.name.encode("utf-8"), launch.id))

    try:
        launch.status = LaunchStatus.objects.get(id=status)
    except ObjectDoesNotExist:
        launch.status = LaunchStatus.objects.get(id=2)

        logger.error("Launch LLID: %s did not have a status." % launch.launch_library_id)
    launch.pad = pad
    launch.launch_service_provider = launch_service_provider
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

    # Check to see if URL exists before adding.
    for url in vid_urls:
        video_found = False
        if launch.vid_urls.all() is not None:
            for each in launch.vid_urls.all():
                if each.vid_url == url:
                    video_found = True
        if not video_found:
            try:
                g = Goose()
                article = g.extract(url=url)
                if article.meta_description is not None and article.meta_description is not "":
                    text = article.meta_description
                elif article.cleaned_text is not None:
                    text = (article.cleaned_text[:300] + '...') if len(article.cleaned_text) > 300 else article.cleaned_text
                else:
                    text = None
                title = ""
                if article.title is not None:
                    title = article.title
                VidURLs.objects.get_or_create(vid_url=url, launch=launch, description=text, title=title, feature_image=article.top_image, priority=10)
            except Exception as e:
                logger.error(e)
    # Check to see if URL exists before adding.
    for url in info_urls:
        info_found = False
        if launch.info_urls.all() is not None:
            for each in launch.info_urls.all():
                if each.info_url == url:
                    info_found = True
        if not info_found:
            try:
                g = Goose()
                article = g.extract(url=url)
                if article.meta_description is not None and article.meta_description is not "":
                    text = article.meta_description
                elif article.cleaned_text is not None:
                    text = (article.cleaned_text[:300] + '...') if len(article.cleaned_text) > 300 else article.cleaned_text
                else:
                    text = None
                title = ""
                if article.title is not None:
                    title = article.title
                InfoURLs.objects.get_or_create(info_url=url, launch=launch, description=text, title=title, feature_image=article.top_image, priority=10)
            except Exception as e:
                logger.error(e)
    launch.mission = get_mission(launch, data)
    launch.rocket = get_rocket(launch, data)
    check_notification(launch)
    launch.save()
    return launch


def check_notification(launch):
    current = datetime.datetime.now(tz=utc)
    if launch.net >= current:
        try:
            if LaunchNotificationRecord.objects.get(launch_id=launch.id) is None:
                LaunchNotificationRecord.objects.get_or_create(launch_id=launch.id)
        except LaunchNotificationRecord.DoesNotExist:
            LaunchNotificationRecord.objects.get_or_create(launch_id=launch.id)


def get_location(data):
    if 'location' in data and data['location'] is not None:
        try:
            location = Location.objects.get(launch_library_id=data['location']['id'])
        except Location.DoesNotExist:
            location = Location(launch_library_id=data['location']['id'],
                                name=data['location']['name'],
                                country_code=data['location']['countryCode'])
            location.save()
        if data['location']['pads'] is not None and len(data['location']['pads']) > 0:
                try:
                    pad = Pad.objects.get(launch_library_id=data['location']['pads'][0]['id'], location=location)
                except Pad.DoesNotExist:
                    pad = Pad(launch_library_id=data['location']['pads'][0]['id'], location=location)
                pad.name = data['location']['pads'][0]['name'].split(',', 1)[0]
                pad.map_url = data['location']['pads'][0]['mapURL']
                pad.wiki_url = data['location']['pads'][0]['wikiURL']
                pad.latitude = data['location']['pads'][0]['latitude']
                if pad.latitude == 0:
                    pad.latitude = 0.0
                pad.longitude = data['location']['pads'][0]['longitude']
                if pad.longitude == 0:
                    pad.longitude = 0.0
                if data['location']['pads'][0]['agencies'] and len(data['location']['pads'][0]['agencies']) > 0:
                    pad.agency_id = data['location']['pads'][0]['agencies'][0]['id']
                pad.save()
                return pad


def get_rocket(launch, data):
    if 'rocket' in data and data['rocket'] is not None:
        try:
            launcher_config = LauncherConfig.objects.get(launch_library_id=data['rocket']['id'])
        except LauncherConfig.DoesNotExist:
            launcher_config = LauncherConfig(launch_library_id=data['rocket']['id'])
            launcher_config.name = data['rocket']['name']
            launcher_config.full_name = data['rocket']['name']
            launcher_config.family_name = data['rocket']['familyname']
            launcher_config.configuration = data['rocket']['configuration']
        if launcher_config.manufacturer is None:
            launcher_config.manufacturer = get_lsp(data)
        launcher_config.save()
        if 'placeholder' not in data['rocket']['imageURL'] and launcher_config.image_url is None:
            download_launcher_image(launcher_config)
        try:
            rocket = Rocket.objects.get(launch__id=launch.id, configuration=launcher_config)
            rocket.configuration = launcher_config
        except Rocket.DoesNotExist:
            rocket = Rocket(configuration=launcher_config)
        rocket.save()
    return rocket


def get_mission(launch, data):
    if data['missions'] is not None and len(data['missions']) > 0:
        try:
            mission = Mission.objects.get(launch_library_id=data['missions'][0]['id'])
        except Mission.DoesNotExist:
            mission = Mission(launch_library_id=data['missions'][0]['id'])
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


def get_lsp(data):
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
