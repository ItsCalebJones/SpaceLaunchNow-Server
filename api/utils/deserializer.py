from api.models import Orbiter, Launcher


def launcher_json_to_model(data):
    name = data['name']
    agency = data['agency']
    nationURL = data['nationURL']
    imageURL = data['imageURL']

    Launcher.objects.create(
        name=name,
        agency=agency,
        nationURL=nationURL,
        imageURL=imageURL
    )


def orbiter_json_to_model(data):
    name = data['name']
    agency = data['agency']
    nationURL = data['nationURL']
    imageURL = data['imageURL']

    Orbiter.objects.create(
        name=name,
        agency=agency,
        nationURL=nationURL,
        imageURL=imageURL
    )
