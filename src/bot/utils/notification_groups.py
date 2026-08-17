"""V6 notification group tables.

Maps raw Launch Library agency and location IDs to the group names used as FCM
attribute topics (``v6_<env>_<group>``).

The server owns ID -> group name; the KMP client owns only the list of group
names it offers users. That split is deliberate: a newly added launch site
starts matching for already-installed clients on the next server deploy, with
no app release. The group *names* below must therefore stay in sync with
``NotificationAgency`` / ``NotificationLocation`` in the KMP app.

Both tables are total: any ID not listed resolves to a catch-all group, so a
launch outside the curated set still produces a well-formed condition rather
than a skipped send.

The two catch-alls are deliberately not symmetric:

- ``otherAgency`` is a *new* user-facing group the app offers, so subscribing to
  it means "agencies I didn't list", which is what the label promises.
- ``unmappedLocation`` is not offered to users at all. The location group named
  ``other`` is already a shipped user-facing row ("Misc. (Sea, Air, etc)")
  meaning exactly IDs 20/3/144, so it must not double as the catch-all —
  otherwise a user who ticked that one row would silently start receiving every
  newly catalogued launch site on Earth. Unlisted locations resolve to a group
  nothing subscribes to, which reproduces V5's behaviour exactly: under V5 the
  device compared the launch's location ID against that same curated list and
  did not match either.

Adding a subscribable "everything else" location row is a product decision, not
a default -- it would mean renaming this constant and shipping a KMP row for it.
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
    # The place, not the agency. Was "isro" until the V6 contract landed; a
    # location named after an agency acronym is what made the collision below
    # possible in the first place.
    "india": (14,),
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
    # Keeps the "Agency" suffix even though the India location is now "india"
    # and nothing collides any more. Agencies and locations share one flat
    # attribute-topic namespace, and a bare "isro" reads as either; the suffix
    # makes it unmistakable. Do not "simplify" this back.
    "isroAgency": (31,),
}

LOCATION_GROUPS: dict[int, str] = {
    location_id: group for group, ids in _LOCATION_GROUP_IDS.items() for location_id in ids
}

AGENCY_GROUPS: dict[int, str] = {agency_id: group for group, ids in _AGENCY_GROUP_IDS.items() for agency_id in ids}

# Not a user-facing row -- see the module docstring on why this is not "other".
DEFAULT_LOCATION_GROUP = "unmappedLocation"
DEFAULT_AGENCY_GROUP = "otherAgency"


def location_group(location_id: int | None) -> str | None:
    """Return the attribute-topic group for a location ID.

    Returns None only when the launch has no location at all; every integer
    resolves to a group, falling back to DEFAULT_LOCATION_GROUP.
    """
    if location_id is None:
        return None
    return LOCATION_GROUPS.get(location_id, DEFAULT_LOCATION_GROUP)


def agency_group(agency_id: int | None) -> str | None:
    """Return the attribute-topic group for an agency ID.

    Returns None only when the launch has no agency at all; every integer
    resolves to a group, falling back to DEFAULT_AGENCY_GROUP.
    """
    if agency_id is None:
        return None
    return AGENCY_GROUPS.get(agency_id, DEFAULT_AGENCY_GROUP)
