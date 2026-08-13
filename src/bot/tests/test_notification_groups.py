"""Tests for the V6 agency/location group tables.

Test-only. Pure data lookups: no DB, no FCM, no Django settings needed.
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

EXPECTED_LOCATION_GROUP_NAMES = {
    "van", "florida", "wallops", "texas", "russia", "frenchGuiana",
    "newZealand", "japan", "isro", "china", "other",
}

EXPECTED_AGENCY_GROUP_NAMES = {
    "spacex", "nasa", "blueOrigin", "rocketLab", "virginGalactic", "ula",
    "arianespace", "roscosmos", "northrop", "casc", "isroAgency", "otherAgency",
}


class LocationGroupTests(SimpleTestCase):
    def test_primary_id_maps_to_its_group(self):
        self.assertEqual(location_group(27), "florida")

    def test_grouped_additional_id_maps_to_the_same_group(self):
        # Cape Canaveral (12) and KSC (27) are one user-facing "Florida".
        self.assertEqual(location_group(12), "florida")

    def test_unknown_id_falls_back_to_the_catch_all(self):
        self.assertEqual(location_group(99999), DEFAULT_LOCATION_GROUP)

    def test_none_is_the_only_unmapped_result(self):
        self.assertIsNone(location_group(None))


class AgencyGroupTests(SimpleTestCase):
    def test_primary_id_maps_to_its_group(self):
        self.assertEqual(agency_group(121), "spacex")

    def test_grouped_additional_id_maps_to_the_same_group(self):
        self.assertEqual(agency_group(193), "roscosmos")

    def test_unknown_id_falls_back_to_the_catch_all(self):
        self.assertEqual(agency_group(99999), DEFAULT_AGENCY_GROUP)

    def test_none_is_the_only_unmapped_result(self):
        self.assertIsNone(agency_group(None))

    def test_isro_agency_does_not_collide_with_the_india_location(self):
        # Attribute topics are one flat namespace shared by agencies and
        # locations. If both used "isro", an India-following user would match
        # ISRO launches from anywhere in the world.
        self.assertEqual(agency_group(31), "isroAgency")
        self.assertEqual(location_group(14), "isro")
        self.assertNotEqual(agency_group(31), location_group(14))


class GroupTableIntegrityTests(SimpleTestCase):
    def test_location_group_names_match_the_spec(self):
        self.assertEqual(set(LOCATION_GROUPS.values()), EXPECTED_LOCATION_GROUP_NAMES)

    def test_agency_group_names_match_the_spec(self):
        names = set(AGENCY_GROUPS.values()) | {DEFAULT_AGENCY_GROUP}
        self.assertEqual(names, EXPECTED_AGENCY_GROUP_NAMES)

    def test_no_location_id_belongs_to_two_groups(self):
        # Built by inverting group->ids; a duplicate would silently win.
        pairs = [(i, g) for g, ids in _location_source().items() for i in ids]
        ids = [i for i, _ in pairs]
        self.assertEqual(len(ids), len(set(ids)), f"duplicate location ids: {pairs}")

    def test_no_agency_id_belongs_to_two_groups(self):
        pairs = [(i, g) for g, ids in _agency_source().items() for i in ids]
        ids = [i for i, _ in pairs]
        self.assertEqual(len(ids), len(set(ids)), f"duplicate agency ids: {pairs}")


def _location_source():
    from bot.utils.notification_groups import _LOCATION_GROUP_IDS

    return _LOCATION_GROUP_IDS


def _agency_source():
    from bot.utils.notification_groups import _AGENCY_GROUP_IDS

    return _AGENCY_GROUP_IDS
