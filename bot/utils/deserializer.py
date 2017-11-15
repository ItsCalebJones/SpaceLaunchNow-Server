from bot.models import Launch, Notification, VidURLs, Pad, Location, Rocket, Mission, LSP, Agency


def launch_json_to_model(data):
    id = data['id']
    name = data['name']
    status = data['status']
    netstamp = data['netstamp']
    wsstamp = data['wsstamp']
    westamp = data['westamp']
    inhold = data['inhold']
    net = data['net']
    window_end = data['windowend']
    window_start = data['windowstart']
    vid_urls = data['vidURLs']

    launch, created = Launch.objects.get_or_create(id=id)
    launch.name = name
    launch.status = status
    launch.netstamp = netstamp
    launch.wsstamp = wsstamp
    launch.westamp = westamp
    launch.inhold = inhold
    launch.net = net
    launch.window_end = window_end
    launch.window_start = window_start
    launch.save()

    launch.vid_urls.all().delete()
    for url in vid_urls:
        VidURLs.objects.create(vid_url=url, launch=launch)
    get_location(launch, data)
    get_rocket(launch, data)
    get_mission(launch, data)
    get_lsp(launch, data)
    check_notification(launch)
    return launch


def check_notification(launch):
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
        location.launch.add(launch)
        location.save()

        if 'pads' in data['location']['pads'] is not None and len(data['location']['pads']) > 0:
                pad, created = Pad.objects.get_or_create(id=data['location']['pads'][0]['id'], location=location)
                pad.name = data['location']['pads'][0]['name']
                pad.map_url = data['location']['pads'][0]['mapURL']
                pad.save()
                if data['location']['pads'][0]['agencies'] is not None and len(data['location']['pads'][0]['agencies']) > 0:
                    agency, created = Agency.objects.get_or_create(id=data['location']['pads'][0]['agencies'][0]['id'])
                    agency.name = data['location']['pads'][0]['agencies'][0]['name']
                    agency.abbrev = data['location']['pads'][0]['agencies'][0]['abbrev']
                    agency.country_code = data['location']['pads'][0]['agencies'][0]['countryCode']
                    agency.pads.add(pad)
                    agency.save()


def get_rocket(launch, data):
    if 'rocket' in data and data['rocket'] is not None:
        rocket, created = Rocket.objects.get_or_create(id=data['rocket']['id'])
        rocket.name = data['rocket']['name']
        rocket.family_name = data['rocket']['familyname']
        rocket.configuration = data['rocket']['configuration']
        if 'placeholder' not in data['rocket']['imageURL']:
            rocket.imageURL = data['rocket']['imageURL']
            if rocket.imageURL is not None:
                launch.img_url = rocket.imageURL
                launch.save()

        rocket.launches.add(launch)
        rocket.save()
        if len(data['rocket']['agencies']) > 0:
            agency, created = Agency.objects.get_or_create(id=data['rocket']['agencies'][0]['id'])
            agency.name = data['rocket']['agencies'][0]['name']
            agency.abbrev = data['rocket']['agencies'][0]['abbrev']
            agency.country_code = data['rocket']['agencies'][0]['countryCode']
            agency.rockets.add(rocket)
            agency.save()


def get_mission(launch, data):
    if data['missions'] is not None and len(data['missions']) > 0:
        mission, created = Mission.objects.get_or_create(id=data['missions'][0]['id'], launch=launch)
        mission.name = data['missions'][0]['name']
        mission.type = data['missions'][0]['type']
        mission.type_name = data['missions'][0]['typeName']
        mission.description = data['missions'][0]['description']
        mission.save()


def get_lsp(launch, data):
    if 'lsp' in data and data['lsp'] is not None:
        lsp, created = LSP.objects.get_or_create(id=data['lsp']['id'])
        lsp.name = data['lsp']['name']
        lsp.country_code = data['lsp']['countryCode']
        lsp.abbrev = data['lsp']['abbrev']
        lsp.launches.add(launch)
        lsp.save()
