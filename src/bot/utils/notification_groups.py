"""V6 notification group tables.

Maps raw Launch Library agency and location IDs to the group names used as FCM
attribute topics (``v6_<env>_<group>``).

The server owns ID -> group name; the KMP client owns only the list of group
names it offers users. That split is deliberate: a newly added launch site
starts matching for already-installed clients on the next server deploy, with
no app release. The group *names* below must therefore stay in sync with
``NotificationAgency`` / ``NotificationLocation`` in the KMP app.

Both tables are total. Any ID not listed resolves to the catch-all group, which
is what keeps strict matching satisfiable for launches outside the curated set.
"""

# group name -> the LL2 IDs that belong to it. Written this way (rather than
# id -> group) because it is the direction a human reviews and edits.
_LOCATION_GROUP_IDS: dict[str, tuple[int, ...]] = {
    "van": (11,),
    "florida": (27, 12),
    "wallops": (21, 1, 25, 31, 155, 162),
    "texas": (143, 29),
    "russia": (15, 5, 6, 18, 30, 146),
    "frenchGuiana": (13,),
    "newZealand": (10,),
    "japan": (24, 26, 32, 166),
    "isro": (14,),
    "china": (17, 8, 16, 19),
    "other": (20, 3, 144),
}

_AGENCY_GROUP_IDS: dict[str, tuple[int, ...]] = {
    "spacex": (121,),
    "nasa": (44,),
    "blueOrigin": (141,),
    "rocketLab": (147,),
    "virginGalactic": (1024,),
    "ula": (124,),
    "arianespace": (115,),
    "roscosmos": (111, 96, 193, 63),
    "northrop": (257,),
    "casc": (88, 194),
    # Renamed from the app's "isro" topicName to avoid colliding with the
    # India *location* group in the shared attribute-topic namespace.
    "isroAgency": (31,),
}

LOCATION_GROUPS: dict[int, str] = {
    location_id: group for group, ids in _LOCATION_GROUP_IDS.items() for location_id in ids
}

AGENCY_GROUPS: dict[int, str] = {
    agency_id: group for group, ids in _AGENCY_GROUP_IDS.items() for agency_id in ids
}

DEFAULT_LOCATION_GROUP = "other"
DEFAULT_AGENCY_GROUP = "otherAgency"


def location_group(location_id: int | None) -> str | None:
    """Return the attribute-topic group for a location ID.

    Returns None only when the launch has no location at all; every integer
    resolves to a group.
    """
    if location_id is None:
        return None
    return LOCATION_GROUPS.get(location_id, DEFAULT_LOCATION_GROUP)


def agency_group(agency_id: int | None) -> str | None:
    """Return the attribute-topic group for an agency ID.

    Returns None only when the launch has no agency at all; every integer
    resolves to a group.
    """
    if agency_id is None:
        return None
    return AGENCY_GROUPS.get(agency_id, DEFAULT_AGENCY_GROUP)
