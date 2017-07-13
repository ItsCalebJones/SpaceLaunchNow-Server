import bot
from bot.models import Launch, Notification


def json_to_model(data):
    id = data['id']
    name = data['name']
    status = data['status']
    netstamp = data['netstamp']
    wsstamp = data['wsstamp']
    westamp = data['westamp']
    inhold = data['inhold']
    rocket_name = data['rocket']['name']
    mission_name = "Unknown"
    if len(data['missions']) > 0:
        mission_name = data['missions'][0]['name']
    if launch.location_name is None:
        launch.location_name = 'Unknown'
    if len(launch.name) > 30:
        launch.name = launch.name.split(" |")[0]
    if len(launch.location_name) > 20:
        launch.location_name = launch.location_name.split(", ")[0]
    location_name = data['location']['name']

    try:
        launch = Launch.objects.get(id=id)
        launch.name = name
        launch.status = status
        launch.netstamp = netstamp
        launch.wsstamp = wsstamp
        launch.westamp = westamp
        launch.inhold = inhold
        launch.rocket_name = rocket_name
        launch.mission_name = mission_name
        launch.location_name = location_name
        launch.save()
        check_notification(launch)
        return launch
    except Launch.DoesNotExist:
        launch = Launch.objects.create(id=id, name=name, status=status, netstamp=netstamp, wsstamp=wsstamp,
                                     westamp=westamp,
                                     inhold=inhold, rocket_name=rocket_name, mission_name=mission_name,
                                     location_name=location_name)
        check_notification(launch)
        return launch


def check_notification(launch):
    try:
        if Notification.objects.get(launch=launch) is None:
            Notification.objects.get_or_create(launch=launch)
    except Notification.DoesNotExist:
        Notification.objects.get_or_create(launch=launch)
