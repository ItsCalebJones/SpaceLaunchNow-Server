"""Conformance tests: server constants must match the shared topic contract.

Test-only. Pure data comparison: no DB, no FCM.

The contract at src/bot/contracts/notification-topics.v6.json is the agreement
between this server and the KMP client about what FCM topics are called. Neither
side errors when they disagree -- the server sends to a topic nobody subscribed
to, or the client subscribes to one nothing sends to, and the notification is
simply never delivered. These tests are the only thing that turns that silence
into a failing build.

The KMP repo runs the mirror of this file against a byte-identical copy.
"""

import json
from pathlib import Path

from django.test import SimpleTestCase

from bot.utils.notification_groups import (
    _AGENCY_GROUP_IDS,
    _LOCATION_GROUP_IDS,
    DEFAULT_AGENCY_GROUP,
    DEFAULT_LOCATION_GROUP,
)
from bot.utils.util import (
    V6_AUDIENCE_CLASSES,
    V6_BROADCAST_KINDS,
    V6_MUTE_EXEMPT_TYPES,
    V6_NOTIFICATION_TYPES,
    V6_STARLINK_MUTED_GROUP,
    build_v6_broadcast_condition,
    build_v6_condition,
    get_v6_attribute_topic,
    get_v6_broadcast_topic,
    get_v6_type_topic,
    v6_class_is_webcast_only,
    v6_class_shape,
)

CONTRACT_PATH = Path(__file__).resolve().parent.parent / "contracts" / "notification-topics.v6.json"


def load_contract() -> dict:
    with CONTRACT_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


CONTRACT = load_contract()


class ContractFileTests(SimpleTestCase):
    def test_the_contract_ships_inside_the_package(self):
        # The Dockerfile copies only src/, so a contract outside it would be
        # absent at runtime and in CI. Keep it importable-adjacent.
        self.assertTrue(CONTRACT_PATH.is_file(), f"missing contract at {CONTRACT_PATH}")

    def test_it_declares_which_scheme_and_version_it_pins(self):
        self.assertEqual(CONTRACT["scheme"], "v6")
        self.assertIsInstance(CONTRACT["version"], int)


class AudienceClassContractTests(SimpleTestCase):
    def test_the_classes_match_the_contract_exactly(self):
        self.assertEqual(list(V6_AUDIENCE_CLASSES), CONTRACT["audienceClasses"]["values"])

    def test_the_webcast_suffix_matches_the_contract(self):
        suffix = CONTRACT["audienceClasses"]["webcastOnlySuffix"]
        for audience_class in V6_AUDIENCE_CLASSES:
            self.assertEqual(
                v6_class_is_webcast_only(audience_class),
                audience_class.endswith(suffix),
                msg=audience_class,
            )

    def test_every_class_reduces_to_a_shape_the_contract_documents(self):
        shapes = set(CONTRACT["audienceClasses"]["shapes"])
        for audience_class in V6_AUDIENCE_CLASSES:
            self.assertIn(v6_class_shape(audience_class), shapes, msg=audience_class)


class NotificationTypeContractTests(SimpleTestCase):
    def test_the_types_match_the_contract_exactly(self):
        self.assertEqual(list(V6_NOTIFICATION_TYPES), CONTRACT["notificationTypes"])


class BroadcastKindContractTests(SimpleTestCase):
    def test_the_wire_tokens_match_the_contract_exactly(self):
        tokens = [kind["token"] for kind in CONTRACT["broadcastKinds"]["values"]]
        self.assertEqual(list(V6_BROADCAST_KINDS), tokens)

    def test_the_server_uses_the_token_and_never_the_client_setting_id(self):
        # The client persists two of these under different ids (featured_news,
        # announcements). Sending to those would reach nothing.
        setting_ids = {kind["clientSettingId"] for kind in CONTRACT["broadcastKinds"]["values"]}
        for setting_id in setting_ids - set(V6_BROADCAST_KINDS):
            with self.subTest(setting_id=setting_id), self.assertRaises(ValueError):
                build_v6_broadcast_condition("prod", "ios", setting_id)


class MuteGroupContractTests(SimpleTestCase):
    def test_the_starlink_mute_group_matches_the_contract(self):
        groups = [group["group"] for group in CONTRACT["muteGroups"]["values"]]
        self.assertIn(V6_STARLINK_MUTED_GROUP, groups)

    def test_the_exempt_types_match_the_contract_exactly(self):
        (starlink,) = [
            group for group in CONTRACT["muteGroups"]["values"] if group["group"] == V6_STARLINK_MUTED_GROUP
        ]
        self.assertEqual(list(V6_MUTE_EXEMPT_TYPES), starlink["exemptTypes"])

    def test_every_exempt_type_is_a_real_notification_type(self):
        for notification_type in V6_MUTE_EXEMPT_TYPES:
            self.assertIn(notification_type, V6_NOTIFICATION_TYPES)

    def test_the_mute_topic_follows_the_attribute_grammar(self):
        self.assertEqual(
            get_v6_attribute_topic("prod", V6_STARLINK_MUTED_GROUP),
            "v6_prod_starlinkMuted",
        )


class GroupContractTests(SimpleTestCase):
    def _contract_groups(self, key) -> list[str]:
        return [group["group"] for group in CONTRACT[key]]

    def test_location_groups_match_the_contract_exactly(self):
        self.assertEqual(
            list(_LOCATION_GROUP_IDS) + [DEFAULT_LOCATION_GROUP],
            self._contract_groups("locationGroups"),
        )

    def test_agency_groups_match_the_contract_exactly(self):
        self.assertEqual(
            list(_AGENCY_GROUP_IDS) + [DEFAULT_AGENCY_GROUP],
            self._contract_groups("agencyGroups"),
        )

    def test_the_contract_agrees_on_which_catch_all_is_offered_to_users(self):
        # The asymmetry is the whole point: otherAgency is a settings row,
        # unmappedLocation deliberately is not. Inverting either silently
        # changes what a shipped toggle means.
        by_name = {group["group"]: group for key in ("locationGroups", "agencyGroups") for group in CONTRACT[key]}
        self.assertFalse(by_name[DEFAULT_LOCATION_GROUP]["subscribable"])
        self.assertTrue(by_name[DEFAULT_AGENCY_GROUP]["subscribable"])

    def test_no_group_name_is_claimed_by_both_tables(self):
        # Attribute topics are one flat namespace; this is what isroAgency exists for.
        locations = set(self._contract_groups("locationGroups"))
        agencies = set(self._contract_groups("agencyGroups"))
        self.assertEqual(locations & agencies, set())

    def test_no_curated_group_is_also_a_catch_all(self):
        for key, default in (
            ("locationGroups", DEFAULT_LOCATION_GROUP),
            ("agencyGroups", DEFAULT_AGENCY_GROUP),
        ):
            source = _LOCATION_GROUP_IDS if key == "locationGroups" else _AGENCY_GROUP_IDS
            self.assertNotIn(default, source, msg=key)


class TopicGrammarContractTests(SimpleTestCase):
    """The builders must produce exactly what the contract's templates describe."""

    def _render(self, template: str, **tokens: str) -> str:
        for name, value in tokens.items():
            template = template.replace("{" + name + "}", value)
        return template

    def test_attribute_topic_matches_the_template(self):
        template = CONTRACT["topicGrammar"]["attribute"]
        self.assertEqual(
            get_v6_attribute_topic("prod", "spacex"),
            self._render(template, env="prod", group="spacex"),
        )

    def test_type_topic_matches_the_template(self):
        template = CONTRACT["topicGrammar"]["type"]
        self.assertEqual(
            get_v6_type_topic("prod", "ios", "strict_w", "partial_failure"),
            self._render(
                template,
                env="prod",
                platform="ios",
                audienceClass="strict_w",
                notificationType="partial_failure",
            ),
        )

    def test_broadcast_topic_matches_the_template(self):
        template = CONTRACT["topicGrammar"]["broadcast"]
        self.assertEqual(
            get_v6_broadcast_topic("debug", "android", "announce"),
            self._render(template, env="debug", platform="android", broadcastKind="announce"),
        )

    def test_the_env_and_platform_tokens_are_the_ones_dispatch_uses(self):
        from bot.app.notifications.v6 import PLATFORMS

        tokens = CONTRACT["topicGrammar"]["tokens"]
        self.assertEqual(sorted(PLATFORMS), sorted(tokens["platform"]))
        # DEBUG toggles between exactly these two.
        self.assertEqual(sorted(tokens["env"]), ["debug", "prod"])

    def test_every_topic_a_real_condition_names_is_contract_shaped(self):
        # Walk the full matrix and confirm each emitted term is a topic the
        # contract's templates can produce -- catches a builder that invents a
        # segment order the client would never subscribe to.
        valid = set()
        for env in ("prod", "debug"):
            for group in self._contract_groups_all():
                valid.add(get_v6_attribute_topic(env, group))
            for platform in ("android", "ios"):
                for audience_class in V6_AUDIENCE_CLASSES:
                    for notification_type in V6_NOTIFICATION_TYPES:
                        valid.add(get_v6_type_topic(env, platform, audience_class, notification_type))

        for env in ("prod", "debug"):
            for platform in ("android", "ios"):
                for audience_class in V6_AUDIENCE_CLASSES:
                    condition, _ = build_v6_condition(
                        env=env,
                        platform=platform,
                        audience_class=audience_class,
                        notification_type="oneHour",
                        agency="spacex",
                        location="florida",
                    )
                    for term in condition.replace("(", "").replace(")", "").split("&&"):
                        topic = term.split("'")[1]
                        self.assertIn(topic, valid, msg=f"{condition} names unknown topic {topic}")

    def _contract_groups_all(self) -> list[str]:
        return [group["group"] for key in ("locationGroups", "agencyGroups") for group in CONTRACT[key]]
