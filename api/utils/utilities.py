

def get_launch_status(status):
    switcher = {
        0: 'Unknown',
        1: 'Go for Launch',
        2: 'Launch is NO-GO',
        3: 'Successful Launch',
        4: 'Launch Failed',
        5: 'Unplanned Hold',
        6: 'In Flight',
        7: 'Partial Failure',
    }
    return switcher.get(status, "Unknown")


def get_agency_type(agency_type):
    switcher = {
        0: 'Unknown',
        1: 'Government',
        2: 'Multinational',
        3: 'Commercial',
        4: 'Educational',
        5: 'Private',
        6: 'Unknown',
    }
    return switcher.get(agency_type, "Unknown")


def get_mission_type(mission_type):
    switcher = {
        0: 'Unknown',
        1: 'Earth Science',
        2: 'Planetary Science',
        3: 'Astrophysics',
        4: 'Heliophysics',
        5: 'Human Exploration',
        6: 'Robotic Exploration',
        7: 'Government/Top Secret',
        8: 'Tourism',
        9: 'Unknown',
        10: 'Communications',
        11: 'Resupply',
        12: 'Suborbital',
        13: 'Test Flight',
        14: 'Dedicated Rideshare',
        15: 'Navigation',
    }
    return switcher.get(mission_type, "Unknown")
