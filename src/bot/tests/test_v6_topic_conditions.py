"""Tests for V6 topic names and FCM condition construction.

Test-only. Pure string building: no DB, no FCM.

The budget test in ConditionBudgetTests is the regression guard for the failure
that caused topic-condition targeting to be rejected in July 2026: FCM permits
at most five topics per condition and degrades silently rather than erroring.
"""

from django.test import SimpleTestCase

from bot.utils.util import (
    V6_AUDIENCE_CLASSES,
    V6_BROADCAST_KINDS,
    V6_NOTIFICATION_TYPES,
    build_v6_broadcast_condition,
    build_v6_condition,
    get_v6_attribute_topic,
    get_v6_broadcast_topic,
    get_v6_type_topic,
    v6_class_is_webcast_only,
    v6_class_shape,
)


def _build(
    audience_class,
    agency="spacex",
    location="florida",
    notification_type="oneHour",
    platform="ios",
    env="prod",
):
    return build_v6_condition(
        env=env,
        platform=platform,
        audience_class=audience_class,
        notification_type=notification_type,
        agency=agency,
        location=location,
    )


def _condition(*args, **kwargs):
    condition, _ = _build(*args, **kwargs)
    return condition


def _reason(*args, **kwargs):
    _, reason = _build(*args, **kwargs)
    return reason


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
    def test_all_class_is_a_single_topic(self):
        self.assertEqual(_condition("all"), "'v6_prod_ios_all_oneHour' in topics")

    def test_flex_class_ors_the_two_attributes(self):
        self.assertEqual(
            _condition("flex"),
            "'v6_prod_ios_flex_oneHour' in topics && ('v6_prod_spacex' in topics || 'v6_prod_florida' in topics)",
        )

    def test_strict_class_ands_the_two_attributes(self):
        self.assertEqual(
            _condition("strict"),
            "'v6_prod_ios_strict_oneHour' in topics && 'v6_prod_spacex' in topics && 'v6_prod_florida' in topics",
        )

    def test_webcast_class_uses_its_own_type_topic(self):
        self.assertIn("v6_prod_ios_flex_w_oneHour", _condition("flex_w"))

    def test_a_built_condition_reports_no_skip_reason(self):
        for audience_class in V6_AUDIENCE_CLASSES:
            condition, reason = _build(audience_class)
            self.assertIsNotNone(condition, msg=audience_class)
            self.assertIsNone(reason, msg=audience_class)


class SkipRuleTests(SimpleTestCase):
    def test_flex_with_only_a_location_uses_a_single_term(self):
        # A LandSpace launch from Jiuquan has no agency group but does map to
        # china; a China-following user must still receive it.
        self.assertEqual(
            _condition("flex", agency=None, location="china"),
            "'v6_prod_ios_flex_oneHour' in topics && 'v6_prod_china' in topics",
        )

    def test_flex_with_only_an_agency_uses_a_single_term(self):
        self.assertEqual(
            _condition("flex", agency="spacex", location=None),
            "'v6_prod_ios_flex_oneHour' in topics && 'v6_prod_spacex' in topics",
        )

    def test_strict_without_an_agency_is_skipped(self):
        # Unsatisfiable: no user's agency selection can match an ungrouped agency.
        self.assertIsNone(_condition("strict", agency=None, location="china"))
        self.assertEqual(_reason("strict", agency=None, location="china"), "unmapped_agency")

    def test_strict_without_a_location_is_skipped(self):
        self.assertIsNone(_condition("strict", agency="spacex", location=None))
        self.assertEqual(_reason("strict", agency="spacex", location=None), "unmapped_location")

    def test_strict_without_either_attribute_names_both(self):
        # Reporting "unmapped_agency" here would send an operator to the wrong
        # table; the launch is missing both.
        self.assertIsNone(_condition("strict", agency=None, location=None))
        self.assertEqual(_reason("strict", agency=None, location=None), "unmapped_attributes")

    def test_flex_with_neither_attribute_is_skipped(self):
        self.assertIsNone(_condition("flex", agency=None, location=None))
        self.assertEqual(_reason("flex", agency=None, location=None), "unmapped_attributes")

    def test_all_class_is_unaffected_by_missing_attributes(self):
        self.assertEqual(_condition("all", agency=None, location=None), "'v6_prod_ios_all_oneHour' in topics")

    def test_an_unknown_notification_type_is_skipped_for_every_class(self):
        # Third skip rule from the design: no device can subscribe to a type
        # topic that is not a real notification type, so the condition is
        # unsatisfiable even for the attribute-free "all" class.
        for audience_class in V6_AUDIENCE_CLASSES:
            condition, reason = _build(audience_class, notification_type="definitely_not_a_type")
            self.assertIsNone(condition, msg=audience_class)
            self.assertEqual(reason, "unknown_type", msg=audience_class)

    def test_an_unknown_audience_class_is_skipped(self):
        # Without this guard an unrecognised class falls through to the flex
        # branch and silently ships flex-shaped targeting for a class that was
        # meant to be something else -- a typo becomes wrong delivery, not an
        # error. Mirrors the notification_type guard.
        for audience_class in ("followAll", "strct", "all_W", ""):
            condition, reason = _build(audience_class)
            self.assertIsNone(condition, msg=audience_class)
            self.assertEqual(reason, "unknown_class", msg=audience_class)

    def test_every_declared_notification_type_still_builds(self):
        # The guard above must not reject the real types it is protecting.
        for notification_type in V6_NOTIFICATION_TYPES:
            condition, reason = _build("all", notification_type=notification_type)
            self.assertIsNotNone(condition, msg=notification_type)
            self.assertIsNone(reason, msg=notification_type)


class ClassDisjointnessTests(SimpleTestCase):
    """A device subscribes to the type topics of exactly one class, and every
    condition is anchored on a class-specific type topic. Distinct type topics
    are therefore what make duplicate delivery impossible -- not any runtime
    deduplication. If two classes ever shared a type topic, a single device
    could match two conditions and get two pushes for one launch."""

    def test_every_class_anchors_on_a_distinct_type_topic(self):
        topics = [get_v6_type_topic("prod", "ios", audience_class, "oneHour") for audience_class in V6_AUDIENCE_CLASSES]
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
            condition = _condition(audience_class)
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
                            condition, _ = _build(
                                audience_class,
                                agency=agency,
                                location=location,
                                notification_type=notification_type,
                                platform=platform,
                            )
                            if condition is not None:
                                yield condition, (platform, audience_class, notification_type, agency, location)

    def test_no_condition_exceeds_three_topics(self):
        for condition, params in self._all_conditions():
            self.assertLessEqual(condition.count("in topics"), 3, msg=f"{params} produced {condition}")

    def test_every_condition_has_balanced_parentheses(self):
        for condition, params in self._all_conditions():
            self.assertEqual(condition.count("("), condition.count(")"), msg=f"{params} produced {condition}")

    def test_every_term_is_a_topic_membership_test(self):
        for condition, params in self._all_conditions():
            self.assertEqual(
                condition.count("' in topics"),
                condition.count("in topics"),
                msg=f"{params} produced {condition}",
            )


class BroadcastConditionTests(SimpleTestCase):
    def test_broadcast_conditions_are_a_single_topic(self):
        for platform in ("ios", "android"):
            for kind in V6_BROADCAST_KINDS:
                condition = build_v6_broadcast_condition("prod", platform, kind)
                self.assertEqual(condition.count("in topics"), 1)

    def test_the_declared_kinds_are_the_three_broadcast_types(self):
        self.assertEqual(set(V6_BROADCAST_KINDS), {"events", "news", "announce"})

    def test_an_unknown_kind_raises_rather_than_targeting_nobody(self):
        # A typo would otherwise build a well-formed condition naming a topic
        # nothing subscribes to: FCM accepts it, the send is counted a success,
        # and the notification reaches zero devices with a green dashboard.
        for kind in ("announcements", "event", "New", ""):
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                build_v6_broadcast_condition("prod", "ios", kind)
