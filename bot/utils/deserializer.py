from bot.models import Launch, Notification, VidURLs


def launch_json_to_model(data):
    id = data['id']
    name = data['name']
    status = data['status']
    netstamp = data['netstamp']
    wsstamp = data['wsstamp']
    westamp = data['westamp']
    inhold = data['inhold']
    img_url = None
    if 'placeholder' not in data['rocket']['imageURL']:
        img_url = data['rocket']['imageURL']
    net = data['net']
    window_end = data['windowend']
    window_start = data['windowstart']
    vid_urls = data['vidURLs']
    rocket_name = data['rocket']['name']
    location_name = data['location']['name']
    mission_name = "Unknown"
    mission_type = ""
    mission_description = ""
    if len(data['missions']) > 0:
        mission_name = data['missions'][0]['name']
        mission_type = data['missions'][0]['typeName']
        mission_description = data['missions'][0]['description']
    if location_name is None:
        location_name = 'Unknown'
    if len(name) > 30:
        name = name.split(" |")[0]
    if len(location_name) > 20:
        location_name = location_name.split(", ")[0]
    lsp_id = None
    lsp_name = ""
    if 'lsp' in data:
        lsp_id = data['lsp']['id']
        lsp_name = data['lsp']['name']

    try:
        launch = Launch.objects.get(id=id)
        launch.name = name
        launch.img_url = img_url
        launch.status = status
        launch.netstamp = netstamp
        launch.wsstamp = wsstamp
        launch.westamp = westamp
        launch.inhold = inhold
        launch.rocket_name = rocket_name
        launch.mission_name = mission_name
        launch.mission_description = mission_description
        launch.mission_type = mission_type
        launch.location_name = location_name
        launch.net = net
        launch.window_end = window_end
        launch.window_start = window_start
        launch.lsp_id = lsp_id
        launch.lsp_name = lsp_name
        launch.save()

        launch.vid_urls.all().delete()
        for url in vid_urls:
            VidURLs.objects.create(vid_url=url, launch=launch)
        check_notification(launch)
        return launch
    except Launch.DoesNotExist:
        launch = Launch.objects.create(id=id, name=name, status=status, netstamp=netstamp, wsstamp=wsstamp,
                                       westamp=westamp, inhold=inhold, rocket_name=rocket_name,
                                       mission_name=mission_name, location_name=location_name, img_url=img_url, net=net,
                                       window_start=window_start, window_end=window_end,
                                       mission_description=mission_description, mission_type=mission_type,
                                       lsp_id=lsp_id, lsp_name=lsp_name)
        for url in vid_urls:
            VidURLs.objects.create(vid_url=url, launch=launch)
        check_notification(launch)
        return launch


def check_notification(launch):
    try:
        if Notification.objects.get(launch=launch) is None:
            Notification.objects.get_or_create(launch=launch)
    except Notification.DoesNotExist:
        Notification.objects.get_or_create(launch=launch)
