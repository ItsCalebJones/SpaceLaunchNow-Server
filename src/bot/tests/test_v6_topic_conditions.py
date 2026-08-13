"""Tests for V6 topic names and FCM condition construction.

Test-only. Pure string building: no DB, no FCM.

The budget test in ConditionBudgetTests is the regression guard for the failure
that caused topic-condition targeting to be rejected in July 2026: FCM permits
at most five topics per condition and degrades silently rather than erroring.
"""

from django.test import SimpleTestCase

from bot.utils.util import (
    V6_AUDIENCE_CLASSES,
    V6_NOTIFICATION_TYPES,
    build_v6_broadcast_condition,
    build_v6_condition,
    get_v6_attribute_topic,
    get_v6_broadcast_topic,
    get_v6_type_topic,
    v6_class_is_webcast_only,
    v6_class_shape,
)


class TopicNameTests(SimpleTestCase):
    def test_attribute_topic_is_env_scoped_and_not_platform_scoped(self):
        self.assertEqual(get_v6_attribute_topic("prod", "spacex"), "v6_prod_spacex")

    def test_type_topic_carries_env_platform_class_and_type(self):
        self.assertEqual(
            get_v6_type_topic("prod", "ios", "flex", "oneHour"),
            "v6_prod_ios_flex_oneHour",
        )

    def test_debug_env_is_reflected_in_the_name(self):
        self.assertEqual(
            get_v6_type_topic("debug", "android", "strict_w", "tenMinutes"),
            "v6_debug_android_strict_w_tenMinutes",
        )

    def test_broadcast_topic_shape(self):
        self.assertEqual(get_v6_broadcast_topic("prod", "ios", "events"), "v6_prod_ios_events")


class ClassHelperTests(SimpleTestCase):
    def test_shape_strips_the_webcast_suffix(self):
        self.assertEqual(v6_class_shape("flex_w"), "flex")
        self.assertEqual(v6_class_shape("strict_w"), "strict")
        self.assertEqual(v6_class_shape("all_w"), "all")

    def test_shape_of_a_plain_class_is_itself(self):
        self.assertEqual(v6_class_shape("flex"), "flex")

    def test_webcast_only_detection(self):
        self.assertTrue(v6_class_is_webcast_only("all_w"))
        self.assertFalse(v6_class_is_webcast_only("all"))

    def test_there_are_exactly_six_classes(self):
        self.assertEqual(
            set(V6_AUDIENCE_CLASSES),
            {"all", "flex", "strict", "all_w", "flex_w", "strict_w"},
        )


class ConditionShapeTests(SimpleTestCase):
    def _build(self, audience_class, agency="spacex", location="florida"):
        return build_v6_condition(
            env="prod",
            platform="ios",
            audience_class=audience_class,
            notification_type="oneHour",
            agency_group=agency,
            location_group=location,
        )

    def test_all_class_is_a_single_topic(self):
        self.assertEqual(self._build("all"), "'v6_prod_ios_all_oneHour' in topics")

    def test_flex_class_ors_the_two_attributes(self):
        self.assertEqual(
            self._build("flex"),
            "'v6_prod_ios_flex_oneHour' in topics "
            "&& ('v6_prod_spacex' in topics || 'v6_prod_florida' in topics)",
        )

    def test_strict_class_ands_the_two_attributes(self):
        self.assertEqual(
            self._build("strict"),
            "'v6_prod_ios_strict_oneHour' in topics "
            "&& 'v6_prod_spacex' in topics && 'v6_prod_florida' in topics",
        )

    def test_webcast_class_uses_its_own_type_topic(self):
        self.assertIn("v6_prod_ios_flex_w_oneHour", self._build("flex_w"))


class SkipRuleTests(SimpleTestCase):
    def _build(self, audience_class, agency, location):
        return build_v6_condition(
            env="prod",
            platform="ios",
            audience_class=audience_class,
            notification_type="oneHour",
            agency_group=agency,
            location_group=location,
        )

    def test_flex_with_only_a_location_uses_a_single_term(self):
        # A LandSpace launch from Jiuquan has no agency group but does map to
        # china; a China-following user must still receive it.
        self.assertEqual(
            self._build("flex", None, "china"),
            "'v6_prod_ios_flex_oneHour' in topics && 'v6_prod_china' in topics",
        )

    def test_flex_with_only_an_agency_uses_a_single_term(self):
        self.assertEqual(
            self._build("flex", "spacex", None),
            "'v6_prod_ios_flex_oneHour' in topics && 'v6_prod_spacex' in topics",
        )

    def test_strict_without_an_agency_is_skipped(self):
        # Unsatisfiable: no user's agency selection can match an ungrouped agency.
        self.assertIsNone(self._build("strict", None, "china"))

    def test_strict_without_a_location_is_skipped(self):
        self.assertIsNone(self._build("strict", "spacex", None))

    def test_flex_with_neither_attribute_is_skipped(self):
        self.assertIsNone(self._build("flex", None, None))

    def test_all_class_is_unaffected_by_missing_attributes(self):
        self.assertEqual(self._build("all", None, None), "'v6_prod_ios_all_oneHour' in topics")


class ClassDisjointnessTests(SimpleTestCase):
    """A device subscribes to the type topics of exactly one class, and every
    condition is anchored on a class-specific type topic. Distinct type topics
    are therefore what make duplicate delivery impossible -- not any runtime
    deduplication. If two classes ever shared a type topic, a single device
    could match two conditions and get two pushes for one launch."""

    def test_every_class_anchors_on_a_distinct_type_topic(self):
        topics = [
            get_v6_type_topic("prod", "ios", audience_class, "oneHour")
            for audience_class in V6_AUDIENCE_CLASSES
        ]
        self.assertEqual(len(topics), len(set(topics)))

    def test_platforms_do_not_share_type_topics(self):
        ios = {get_v6_type_topic("prod", "ios", c, "oneHour") for c in V6_AUDIENCE_CLASSES}
        android = {get_v6_type_topic("prod", "android", c, "oneHour") for c in V6_AUDIENCE_CLASSES}
        self.assertEqual(ios & android, set())

    def test_environments_do_not_share_type_topics(self):
        prod = {get_v6_type_topic("prod", "ios", c, "oneHour") for c in V6_AUDIENCE_CLASSES}
        debug = {get_v6_type_topic("debug", "ios", c, "oneHour") for c in V6_AUDIENCE_CLASSES}
        self.assertEqual(prod & debug, set())

    def test_a_condition_never_references_another_class_type_topic(self):
        for audience_class in V6_AUDIENCE_CLASSES:
            condition = build_v6_condition(
                env="prod",
                platform="ios",
                audience_class=audience_class,
                notification_type="oneHour",
                agency_group="spacex",
                location_group="florida",
            )
            for other in V6_AUDIENCE_CLASSES:
                if other == audience_class:
                    continue
                self.assertNotIn(
                    f"'{get_v6_type_topic('prod', 'ios', other, 'oneHour')}' in topics",
                    condition,
                    msg=f"{audience_class} condition references {other}",
                )


class ConditionBudgetTests(SimpleTestCase):
    """Every emitted condition must stay within the FCM topic ceiling."""

    def _all_conditions(self):
        for platform in ("ios", "android"):
            for audience_class in V6_AUDIENCE_CLASSES:
                for notification_type in V6_NOTIFICATION_TYPES:
                    for agency in ("spacex", None):
                        for location in ("florida", None):
                            condition = build_v6_condition(
                                env="prod",
                                platform=platform,
                                audience_class=audience_class,
                                notification_type=notification_type,
                                agency_group=agency,
                                location_group=location,
                            )
                            if condition is not None:
                                yield condition, (platform, audience_class, notification_type, agency, location)

    def test_no_condition_exceeds_three_topics(self):
        for condition, params in self._all_conditions():
            self.assertLessEqual(
                condition.count("in topics"), 3, msg=f"{params} produced {condition}"
            )

    def test_every_condition_has_balanced_parentheses(self):
        for condition, params in self._all_conditions():
            self.assertEqual(
                condition.count("("), condition.count(")"), msg=f"{params} produced {condition}"
            )

    def test_every_term_is_a_topic_membership_test(self):
        for condition, params in self._all_conditions():
            self.assertEqual(
                condition.count("' in topics"),
                condition.count("in topics"),
                msg=f"{params} produced {condition}",
            )

    def test_broadcast_conditions_are_a_single_topic(self):
        for platform in ("ios", "android"):
            for kind in ("events", "news", "announce"):
                condition = build_v6_broadcast_condition("prod", platform, kind)
                self.assertEqual(condition.count("in topics"), 1)
