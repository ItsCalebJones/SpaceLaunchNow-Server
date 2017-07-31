from api.models import Orbiter, Launcher, LauncherDetail


def launcher_json_to_model(data):
    name = data['name']
    agency = data['agency']
    nation_url = data['nationURL']
    image_url = data['imageURL']

    Launcher.objects.create(
        name=name,
        agency=agency,
        nation_url=nation_url,
        image_url=image_url
    )


def orbiter_json_to_model(data):
    name = data['name']
    agency = data['agency']
    nation_url = data['nationURL']
    image_url = data['imageURL']
    history = data['history']
    details = data['details']
    wiki_link = data['wikiLink']

    Orbiter.objects.create(
        name=name,
        agency=agency,
        nation_url=nation_url,
        image_url=image_url,
        history=history,
        details=details,
        wiki_link=wiki_link
    )


def launch_detail_to_model(data):
    name = data['LV_Name']
    try:
        description = data['Description']
    except KeyError as e:
        description = ""
    family = data['LV_Family']
    s_family = data['LV_SFamily']
    manufacturer = data['LV_Manufacturer']
    variant = data['LV_Variant']
    alias = data['LV_Alias']
    min_stage = data['Min_Stage']
    max_stage = data['Max_Stage']
    length = data['Length']
    diameter = data['Diameter']
    launch_mass = data['Launch_Mass']
    leo_capacity = data['LEO_Capacity']
    gto_capacity = data['GTO_Capacity']
    to_thrust = data['TO_Thrust']
    vehicle_class = data['Class']
    apogee = data['Apogee']
    vehicle_range = data['Range']
    image_url = data['ImageURL']
    try:
        info_url = data['InfoURL']
    except KeyError as e:
        info_url = ""
    try:
        wiki_url = data['WikiURL']
    except KeyError as e:
        wiki_url = ""

    LauncherDetail.objects.create(
        name=name,
        description=description,
        family=family,
        s_family=s_family,
        manufacturer=manufacturer,
        variant=variant,
        alias=alias,
        min_stage=min_stage,
        max_stage=max_stage,
        length=length,
        diameter=diameter,
        launch_mass=launch_mass,
        leo_capacity=leo_capacity,
        gto_capacity=gto_capacity,
        to_thrust=to_thrust,
        vehicle_class=vehicle_class,
        apogee=apogee,
        vehicle_range=vehicle_range,
        image_url=image_url,
        info_url=info_url,
        wiki_url=wiki_url
    )
