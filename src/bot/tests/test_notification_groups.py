"""Tests for the V6 agency/location group tables.

Test-only. Pure data lookups: no DB, no FCM, no Django settings needed.

The ID -> group mapping is pinned in full below, transcribed from the design
spec's tables rather than read back from the implementation. That is the part
that decides who receives a launch: dropping 12 from `florida` leaves every
group *name* intact, so a names-only assertion stays green while every Cape
Canaveral launch silently stops reaching `v6_prod_florida` subscribers.
"""

from django.test import SimpleTestCase

from bot.utils.notification_groups import (
    AGENCY_GROUPS,
    DEFAULT_AGENCY_GROUP,
    DEFAULT_LOCATION_GROUP,
    LOCATION_GROUPS,
    agency_group,
    location_group,
)

# Transcribed from 2026-08-13-v6-topic-targeted-notifications-design.md, "Location".
SPEC_LOCATION_GROUP_IDS = {
    "van": (11,),
    "florida": (27, 12),
    "wallops": (21, 1, 25, 31, 155, 162),
    "texas": (143, 29),
    "russia": (15, 5, 6, 18, 30, 146),
    "frenchGuiana": (13,),
    "newZealand": (10,),
    "japan": (24, 26, 32, 166),
    "india": (14,),
    "china": (17, 8, 16, 19),
    "other": (20, 3, 144),
}

# Transcribed from the same spec, "Agency".
SPEC_AGENCY_GROUP_IDS = {
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
    "isroAgency": (31,),
}


class LocationGroupTests(SimpleTestCase):
    def test_every_spec_id_maps_to_its_spec_group(self):
        for group, ids in SPEC_LOCATION_GROUP_IDS.items():
            for location_id in ids:
                with self.subTest(group=group, location_id=location_id):
                    self.assertEqual(location_group(location_id), group)

    def test_the_table_contains_nothing_beyond_the_spec(self):
        expected = {i: g for g, ids in SPEC_LOCATION_GROUP_IDS.items() for i in ids}
        self.assertEqual(LOCATION_GROUPS, expected)

    def test_unknown_id_falls_back_to_the_catch_all(self):
        self.assertEqual(location_group(99999), DEFAULT_LOCATION_GROUP)

    def test_the_catch_all_is_not_the_user_facing_other_group(self):
        # "other" is a shipped settings row ("Misc. (Sea, Air, etc)") meaning
        # exactly IDs 20/3/144. If the catch-all reused that name, a user who
        # ticked that one row would start receiving every newly catalogued
        # launch site on Earth -- a silent widening of a toggle they set under
        # V5. Unlisted IDs must land somewhere nothing subscribes to.
        self.assertNotEqual(DEFAULT_LOCATION_GROUP, "other")
        self.assertNotIn(DEFAULT_LOCATION_GROUP, LOCATION_GROUPS.values())
        self.assertEqual(location_group(20), "other")
        self.assertNotEqual(location_group(99999), "other")

    def test_none_is_the_only_unmapped_result(self):
        self.assertIsNone(location_group(None))


class AgencyGroupTests(SimpleTestCase):
    def test_every_spec_id_maps_to_its_spec_group(self):
        for group, ids in SPEC_AGENCY_GROUP_IDS.items():
            for agency_id in ids:
                with self.subTest(group=group, agency_id=agency_id):
                    self.assertEqual(agency_group(agency_id), group)

    def test_the_table_contains_nothing_beyond_the_spec(self):
        expected = {i: g for g, ids in SPEC_AGENCY_GROUP_IDS.items() for i in ids}
        self.assertEqual(AGENCY_GROUPS, expected)

    def test_unknown_id_falls_back_to_the_catch_all(self):
        self.assertEqual(agency_group(99999), DEFAULT_AGENCY_GROUP)

    def test_the_agency_catch_all_is_a_group_of_its_own(self):
        # Unlike the location catch-all, otherAgency is meant to be offered to
        # users as "Other Agencies" -- but it still must not double as a curated
        # group, or its subscribers would inherit whatever that group means.
        self.assertNotIn(DEFAULT_AGENCY_GROUP, AGENCY_GROUPS.values())

    def test_none_is_the_only_unmapped_result(self):
        self.assertIsNone(agency_group(None))

    def test_isro_agency_does_not_collide_with_the_india_location(self):
        # Attribute topics are one flat namespace shared by agencies and
        # locations. If both used "isro", an India-following user would match
        # ISRO launches from anywhere in the world. Two guards now stand
        # against that -- the location is named for the place, and the agency
        # keeps its suffix -- and this pins both.
        self.assertEqual(agency_group(31), "isroAgency")
        self.assertEqual(location_group(14), "india")
        self.assertNotEqual(agency_group(31), location_group(14))

    def test_no_group_is_named_for_an_agency_acronym_on_the_location_side(self):
        # The original defect was a *location* called "isro". Naming a place
        # after an agency is what let the two tables reach for the same name.
        self.assertNotIn("isro", LOCATION_GROUPS.values())


class GroupTableIntegrityTests(SimpleTestCase):
    def test_no_location_id_belongs_to_two_groups(self):
        # Built by inverting group->ids; a duplicate would silently win.
        pairs = [(i, g) for g, ids in _location_source().items() for i in ids]
        ids = [i for i, _ in pairs]
        self.assertEqual(len(ids), len(set(ids)), f"duplicate location ids: {pairs}")

    def test_no_agency_id_belongs_to_two_groups(self):
        pairs = [(i, g) for g, ids in _agency_source().items() for i in ids]
        ids = [i for i, _ in pairs]
        self.assertEqual(len(ids), len(set(ids)), f"duplicate agency ids: {pairs}")

    def test_agency_and_location_group_names_never_collide(self):
        # One flat attribute-topic namespace across both tables.
        shared = (set(LOCATION_GROUPS.values()) | {DEFAULT_LOCATION_GROUP}) & (
            set(AGENCY_GROUPS.values()) | {DEFAULT_AGENCY_GROUP}
        )
        self.assertEqual(shared, set(), f"group names used by both tables: {shared}")


def _location_source():
    from bot.utils.notification_groups import _LOCATION_GROUP_IDS

    return _LOCATION_GROUP_IDS


def _agency_source():
    from bot.utils.notification_groups import _AGENCY_GROUP_IDS

    return _AGENCY_GROUP_IDS
