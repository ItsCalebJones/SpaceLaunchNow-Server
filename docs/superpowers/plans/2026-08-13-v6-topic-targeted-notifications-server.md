# V6 Topic-Targeted Notification Delivery (Server) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make SLN-Server target launch and broadcast notifications with FCM topic conditions derived from each launch's own attributes, so devices receive only what they should display.

**Architecture:** A total ID→group-name table maps each launch's agency and location to a topic group. A pure condition builder turns (env, platform, audience class, notification type, groups) into an FCM condition of at most three topics. A `V6NotificationMixin` iterates a six-entry audience-class table and dispatches one send per satisfiable class, alongside the existing V5 broadcast (dual-send). Nothing in V5 is removed.

**Tech Stack:** Python 3, Django, `pyfcm` via the existing `NotificationService.fcm` wrapper, `prometheus_client`, Django test runner (`SimpleTestCase`), Docker Compose test stack.

**Spec:** `docs/superpowers/specs/2026-08-13-v6-topic-targeted-notifications-design.md`
**Companion (client, ships second):** `SpaceLaunchNow-KMP-Main/docs/superpowers/specs/2026-08-13-v6-topic-targeted-notifications-kmp-design.md`

## Global Constraints

- **Every generated condition contains at most 3 topics.** FCM's ceiling is 5; the 2-topic margin is deliberate. This is the failure that caused topic targeting to be rejected in July 2026 — it is enforced by test, not convention.
- **Topic name formats are exact and shared with the client.** Attribute: `v6_<env>_<group>`. Type: `v6_<env>_<platform>_<class>_<type>`. Broadcast: `v6_<env>_<platform>_<kind>`.
- `env` ∈ `{prod, debug}` — `debug` when `self.DEBUG` is true. `platform` ∈ `{ios, android}`. `kind` ∈ `{events, news, announce}`.
- **Audience classes:** `all`, `flex`, `strict`, `all_w`, `flex_w`, `strict_w`. The `_w` suffix means webcast-only and those classes are targeted **only** when the launch has a webcast.
- **The payload is unchanged.** V6 reuses `_build_v5_data_payload` verbatim. No fields added, renamed, or removed.
- **iOS APNs config is unchanged:** `apns-priority: 10`, `apns-collapse-id: <launch_uuid>`, `aps.mutable-content: 1`. Android config unchanged: `priority: high`, `collapse_key: <launch_uuid>`, `ttl: 86400s`.
- **V5 dual-send stays.** No V5 send site is removed, disabled, or reordered by this plan. Retirement is a separate future PR.
- **Group tables are total** — every agency/location ID resolves to a group, with `other` / `otherAgency` absorbing the tail.
- **Attribute topics use group names, never raw IDs.** No group-name→IDs inverse map is built server-side; nothing needs it.
- **Commit messages are one line, subject only, and carry no `Co-Authored-By` trailer.**

## Running Tests

The suite runs in Docker. Credentials must be bridged into env vars **in the same shell** as the compose command (the private `tsd` index password lives in the Windows keyring under service `poetry-repository-tsd`, not in `poetry config`):

```bash
export POETRY_HTTP_BASIC_TSD_USERNAME=<username from %APPDATA%\pypoetry\auth.toml>
export POETRY_HTTP_BASIC_TSD_PASSWORD=$(python -c "import keyring; print(keyring.get_password('poetry-repository-tsd', '<username>'))")
```

**Targeted run (use this for the inner TDD loop — seconds, not minutes):**

```bash
docker compose -f docker/docker-compose.test.yml run --rm test \
  python manage.py test bot.tests.test_v6_topic_conditions --settings=spacelaunchnow.settings.test
```

**Full suite (run at the end of each task before committing):**

```bash
docker compose -f docker/docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test
```

The first build is slow; dependency layers cache afterwards. All tests added by this plan are `SimpleTestCase` — no database, no live FCM.

## File Structure

| File | Responsibility |
|---|---|
| `src/bot/utils/notification_groups.py` | **New.** The two group tables and their lookup helpers. Data only — no FCM, no Django. |
| `src/bot/utils/util.py` | **Modify.** Adds V6 topic-name helpers and the pure condition builder. V3/V4/V5 helpers untouched. |
| `src/bot/app/notifications/metrics.py` | **Modify.** Adds the `audience_class` label and a skip counter. |
| `src/bot/app/notifications/v6.py` | **New.** `V6NotificationMixin` — class table, per-class dispatch, skip handling, platform send methods. |
| `src/bot/app/notifications/notification_handler.py` | **Modify.** Composes the mixin; launch dispatch calls V6 alongside V5. |
| `src/bot/app/events/notification_handler.py` | **Modify.** Adds a V6 broadcast send for events. |
| `src/bot/app/notifications/news_notification_handler.py` | **Modify.** Adds a V6 broadcast send for news. |
| `src/bot/app/notifications/custom.py` | **Modify.** Adds a V6 broadcast send for custom announcements. |
| `src/bot/tests/test_notification_groups.py` | **New.** Group table totality, disjointness, lookups. |
| `src/bot/tests/test_v6_topic_conditions.py` | **New.** Topic names, condition shapes, skip rules, the ≤3 budget guard. |
| `src/bot/tests/test_v6_dispatch.py` | **New.** Which conditions get emitted per launch, and that V5 still fires. |

---

### Task 1: Group tables and lookups

**Files:**
- Create: `src/bot/utils/notification_groups.py`
- Test: `src/bot/tests/test_notification_groups.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `LOCATION_GROUPS: dict[int, str]`, `AGENCY_GROUPS: dict[int, str]`
  - `DEFAULT_LOCATION_GROUP: str = "other"`, `DEFAULT_AGENCY_GROUP: str = "otherAgency"`
  - `location_group(location_id: int | None) -> str | None`
  - `agency_group(agency_id: int | None) -> str | None`

Both lookups return `None` **only** for a `None` input; any integer resolves to a group. That distinction matters: `None` means "this launch has no location/agency at all", which is the only case the condition builder treats as unmapped.

- [ ] **Step 1: Write the failing test**

Create `src/bot/tests/test_notification_groups.py`:

```python
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
docker compose -f docker/docker-compose.test.yml run --rm test \
  python manage.py test bot.tests.test_notification_groups --settings=spacelaunchnow.settings.test
```
Expected: FAIL — `ModuleNotFoundError: No module named 'bot.utils.notification_groups'`.

- [ ] **Step 3: Write the implementation**

Create `src/bot/utils/notification_groups.py`:

```python
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
```

- [ ] **Step 4: Run the test to verify it passes**

Run the same command as Step 2. Expected: PASS, 13 tests.

- [ ] **Step 5: Run the full suite**

```bash
docker compose -f docker/docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test
```
Expected: PASS. Nothing imports the new module yet, so no existing test can regress.

- [ ] **Step 6: Commit**

```bash
git add src/bot/utils/notification_groups.py src/bot/tests/test_notification_groups.py
git commit -m "feat(notifications): add V6 agency and location group tables"
```

---

### Task 2: V6 topic names and the condition builder

**Files:**
- Modify: `src/bot/utils/util.py` (append at end of file; do not touch the V3 helpers at lines 49-289 or the V4/V5 helpers at lines 357-397)
- Test: `src/bot/tests/test_v6_topic_conditions.py`

**Interfaces:**
- Consumes: nothing from Task 1 (the builder takes already-resolved group names as strings).
- Produces:
  - `V6_AUDIENCE_CLASSES: tuple[str, ...]`
  - `V6_NOTIFICATION_TYPES: tuple[str, ...]`
  - `v6_class_shape(audience_class: str) -> str`
  - `v6_class_is_webcast_only(audience_class: str) -> bool`
  - `get_v6_attribute_topic(env: str, group: str) -> str`
  - `get_v6_type_topic(env: str, platform: str, audience_class: str, notification_type: str) -> str`
  - `get_v6_broadcast_topic(env: str, platform: str, kind: str) -> str`
  - `build_v6_condition(*, env, platform, audience_class, notification_type, agency_group, location_group) -> str | None`
  - `build_v6_broadcast_condition(env: str, platform: str, kind: str) -> str`

- [ ] **Step 1: Write the failing test**

Create `src/bot/tests/test_v6_topic_conditions.py`:

```python
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
docker compose -f docker/docker-compose.test.yml run --rm test \
  python manage.py test bot.tests.test_v6_topic_conditions --settings=spacelaunchnow.settings.test
```
Expected: FAIL — `ImportError: cannot import name 'V6_AUDIENCE_CLASSES' from 'bot.utils.util'`.

- [ ] **Step 3: Write the implementation**

Append to the end of `src/bot/utils/util.py`:

```python
# --------------------------------------------------------------------------
# V6 topic-targeted delivery
#
# The condition names the *launch's* attributes; the device's subscription set
# performs the match. Every condition below contains at most 3 topics against
# FCM's ceiling of 5 -- see test_v6_topic_conditions.ConditionBudgetTests.
# --------------------------------------------------------------------------

V6_AUDIENCE_CLASSES: tuple[str, ...] = (
    "all",
    "flex",
    "strict",
    "all_w",
    "flex_w",
    "strict_w",
)

V6_NOTIFICATION_TYPES: tuple[str, ...] = (
    "twentyFourHour",
    "oneHour",
    "tenMinutes",
    "oneMinute",
    "netstampChanged",
    "webcastLive",
    "inFlight",
    "success",
    "failure",
    "partial_failure",
)

_V6_WEBCAST_SUFFIX = "_w"


def v6_class_shape(audience_class: str) -> str:
    """Return the matching shape of a class: 'all', 'flex', or 'strict'."""
    if audience_class.endswith(_V6_WEBCAST_SUFFIX):
        return audience_class[: -len(_V6_WEBCAST_SUFFIX)]
    return audience_class


def v6_class_is_webcast_only(audience_class: str) -> bool:
    """Whether this class only wants launches that have a webcast."""
    return audience_class.endswith(_V6_WEBCAST_SUFFIX)


def get_v6_attribute_topic(env: str, group: str) -> str:
    """Attribute topic. Shared across platforms: the type topic carries platform."""
    return f"v6_{env}_{group}"


def get_v6_type_topic(env: str, platform: str, audience_class: str, notification_type: str) -> str:
    """Type topic. The audience class lives here, which is what keeps the
    classes disjoint and makes duplicate delivery structurally impossible."""
    return f"v6_{env}_{platform}_{audience_class}_{notification_type}"


def get_v6_broadcast_topic(env: str, platform: str, kind: str) -> str:
    """Broadcast topic for events / news / announce."""
    return f"v6_{env}_{platform}_{kind}"


def _v6_term(topic: str) -> str:
    return f"'{topic}' in topics"


def build_v6_condition(
    *,
    env: str,
    platform: str,
    audience_class: str,
    notification_type: str,
    agency_group: str | None,
    location_group: str | None,
) -> str | None:
    """Build the FCM condition for one audience class, or None to skip.

    None means the condition would be unsatisfiable and must not be sent:
    a strict class needs both attributes, a flexible class needs at least one.
    """
    type_term = _v6_term(get_v6_type_topic(env, platform, audience_class, notification_type))
    shape = v6_class_shape(audience_class)

    if shape == "all":
        return type_term

    agency_term = _v6_term(get_v6_attribute_topic(env, agency_group)) if agency_group else None
    location_term = _v6_term(get_v6_attribute_topic(env, location_group)) if location_group else None

    if shape == "strict":
        if not (agency_term and location_term):
            return None
        return f"{type_term} && {agency_term} && {location_term}"

    attribute_terms = [term for term in (agency_term, location_term) if term]
    if not attribute_terms:
        return None
    if len(attribute_terms) == 1:
        return f"{type_term} && {attribute_terms[0]}"
    return f"{type_term} && ({attribute_terms[0]} || {attribute_terms[1]})"


def build_v6_broadcast_condition(env: str, platform: str, kind: str) -> str:
    """Broadcast types are gated by their own toggle only -- a single topic."""
    return _v6_term(get_v6_broadcast_topic(env, platform, kind))
```

- [ ] **Step 4: Run the test to verify it passes**

Run the same command as Step 2. Expected: PASS, 26 tests.

- [ ] **Step 5: Run the full suite**

```bash
docker compose -f docker/docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test
```
Expected: PASS. `util.py` gained only new symbols.

- [ ] **Step 6: Commit**

```bash
git add src/bot/utils/util.py src/bot/tests/test_v6_topic_conditions.py
git commit -m "feat(notifications): add V6 topic names and condition builder"
```

---

### Task 3: Metrics for audience class and skips

**Files:**
- Modify: `src/bot/app/notifications/metrics.py:17-50`
- Test: `src/bot/tests/test_notification_metrics.py` (existing file — add a class)

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `record_send(platform, category, success, result=None, audience_class="none")` — the new keyword is optional and defaults so all existing call sites keep working unchanged.
  - `record_skip(platform: str, audience_class: str, reason: str) -> None`
  - `NOTIFICATION_SENDS_SKIPPED` counter.

Adding a label to `NOTIFICATIONS_SENT` starts new Prometheus series. Dashboard queries that aggregate without grouping by `audience_class` are unaffected; any query pinning the exact label set would need updating. None do today.

- [ ] **Step 1: Update the existing helper, then write the failing test**

`REGISTRY.get_sample_value` matches the label dict **exactly**, so the existing `_sent()` helper at `src/bot/tests/test_notification_metrics.py:24-32` returns `None` the moment a fourth label exists — which would break every test in `RecordSendTests`. Update it to carry the new label with a default that matches `record_send`'s, so the existing call sites keep working untouched:

```python
def _sent(platform, category, result, audience_class="none"):
    return (
        REGISTRY.get_sample_value(
            "sln_notifications_sent_total",
            {
                "platform": platform,
                "category": category,
                "result": result,
                "audience_class": audience_class,
            },
        )
        or 0.0
    )


def _skipped(platform, audience_class, reason):
    return (
        REGISTRY.get_sample_value(
            "sln_notification_sends_skipped_total",
            {"platform": platform, "audience_class": audience_class, "reason": reason},
        )
        or 0.0
    )
```

Then append this test class to the same file:

```python
class AudienceClassMetricTests(SimpleTestCase):
    def test_existing_callers_land_on_the_default_audience_class(self):
        before = _sent("ios", "launch", "success")
        metrics.record_send(platform="ios", category="launch", success=True)
        self.assertEqual(_sent("ios", "launch", "success"), before + 1)

    def test_audience_class_is_labelled_when_given(self):
        before = _sent("ios", "launch", "success", "strict")
        metrics.record_send(platform="ios", category="launch", success=True, audience_class="strict")
        self.assertEqual(_sent("ios", "launch", "success", "strict"), before + 1)

    def test_classes_are_counted_separately(self):
        before_flex = _sent("android", "launch", "success", "flex")
        before_strict = _sent("android", "launch", "success", "strict")
        metrics.record_send(platform="android", category="launch", success=True, audience_class="flex")
        self.assertEqual(_sent("android", "launch", "success", "flex"), before_flex + 1)
        self.assertEqual(_sent("android", "launch", "success", "strict"), before_strict)

    def test_record_skip_increments_the_skip_counter(self):
        before = _skipped("ios", "strict", "unmapped_agency")
        metrics.record_skip(platform="ios", audience_class="strict", reason="unmapped_agency")
        self.assertEqual(_skipped("ios", "strict", "unmapped_agency"), before + 1)
```

`SimpleTestCase`, `REGISTRY`, and `metrics` are already imported at the top of this file.

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
docker compose -f docker/docker-compose.test.yml run --rm test \
  python manage.py test bot.tests.test_notification_metrics --settings=spacelaunchnow.settings.test
```
Expected: FAIL — `AttributeError: module 'bot.app.notifications.metrics' has no attribute 'record_skip'`, plus assertion failures in the other three new tests (`0.0 != 1.0`), because `get_sample_value` returns `None` for a label set the counter does not have. The pre-existing `RecordSendTests` will **also** fail at this point for the same reason; Step 3 fixes both.

- [ ] **Step 3: Write the implementation**

In `src/bot/app/notifications/metrics.py`, replace the `NOTIFICATIONS_SENT` definition and `record_send`, and add the skip counter:

```python
# platform: android|ios, category: launch|news|event|custom,
# result: success|error, audience_class: V6 class name or "none" for V5 sends
NOTIFICATIONS_SENT = Counter(
    "sln_notifications_sent_total",
    "FCM notification send attempts by platform, category, result, and audience class.",
    ["platform", "category", "result", "audience_class"],
)

# Sends not attempted because the condition would have been unsatisfiable.
# A rising unmapped_* count means the group table has a gap.
NOTIFICATION_SENDS_SKIPPED = Counter(
    "sln_notification_sends_skipped_total",
    "V6 sends skipped because the audience-class condition was unsatisfiable.",
    ["platform", "audience_class", "reason"],
)


def record_send(platform: str, category: str, success: bool, result=None, audience_class: str = "none") -> None:
    """Record one FCM send attempt beside the existing log lines.

    Args:
        platform: "android" or "ios".
        category: "launch", "news", "event", or "custom".
        success: whether the send raised (False) or returned (True).
        result: the raw FCM response; used to extract a recipient count
            when the response carries one.
        audience_class: the V6 audience class, or "none" for V5 broadcasts.
    """
    NOTIFICATIONS_SENT.labels(
        platform=platform,
        category=category,
        result="success" if success else "error",
        audience_class=audience_class,
    ).inc()
    if success:
        recipients = _extract_success_count(result)
        if recipients > 0:
            NOTIFICATION_RECIPIENTS.labels(platform=platform, category=category).inc(recipients)


def record_skip(platform: str, audience_class: str, reason: str) -> None:
    """Record a V6 send that was not attempted because it was unsatisfiable."""
    NOTIFICATION_SENDS_SKIPPED.labels(
        platform=platform, audience_class=audience_class, reason=reason
    ).inc()
```

- [ ] **Step 4: Run the test to verify it passes**

Run the same command as Step 2. Expected: PASS — including the pre-existing `test_topic_response_without_count_does_not_move_recipients`, which must still pass unchanged.

- [ ] **Step 5: Run the full suite**

```bash
docker compose -f docker/docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test
```
Expected: PASS, including the four pre-existing `RecordSendTests` cases, which now resolve through the updated `_sent()` default. If any of them still fail, the helper edit in Step 1 was missed.

- [ ] **Step 6: Commit**

```bash
git add src/bot/app/notifications/metrics.py src/bot/tests/test_notification_metrics.py
git commit -m "feat(notifications): label sends by audience class and count skips"
```

---

### Task 4: V6 launch dispatch mixin

**Files:**
- Create: `src/bot/app/notifications/v6.py`
- Test: `src/bot/tests/test_v6_dispatch.py`

**Interfaces:**
- Consumes: `location_group` / `agency_group` (Task 1); `V6_AUDIENCE_CLASSES`, `v6_class_is_webcast_only`, `build_v6_condition`, `build_v6_broadcast_condition` (Task 2); `record_send`, `record_skip` (Task 3); `_build_v5_data_payload` from `V5NotificationMixin` via the MRO.
- Produces:
  - `V6NotificationMixin.send_v6_launch_notification(launch, notification_type, contents) -> list[NotificationResult]`
  - `V6NotificationMixin.send_v6_broadcast(kind, v5_data, title, body, collapse_id, category) -> list[NotificationResult]`

`V6NotificationMixin` depends on `V5NotificationMixin` for the payload builder so the two schemes are guaranteed to ship identical payloads. When V5 is retired, `_build_v5_data_payload` moves into this module — that is the only coupling to unwind.

- [ ] **Step 1: Write the failing test**

Create `src/bot/tests/test_v6_dispatch.py`:

```python
"""Tests for V6 per-audience-class dispatch.

Test-only. self.fcm is mocked and every payload is stubbed; no DB, no FCM.
"""

from unittest import mock

from django.test import SimpleTestCase

from bot.app.notifications.v5 import V5NotificationMixin
from bot.app.notifications.v6 import V6NotificationMixin

PAYLOAD = {
    "notification_type": "oneHour",
    "launch_uuid": "uuid-123",
    "title": "Falcon 9",
    "body": "Launch attempt in one hour.",
    "webcast": "True",
}


class _Handler(V6NotificationMixin, V5NotificationMixin):
    """The production handler composes both mixins; mirror that here."""


def _conditions(fcm_mock) -> list[str]:
    return [call.kwargs["topic_condition"] for call in fcm_mock.notify.call_args_list]


class LaunchDispatchTests(SimpleTestCase):
    def setUp(self):
        self.handler = _Handler()
        self.handler.fcm = mock.MagicMock()
        self.handler.DEBUG = False

    def _dispatch(self, payload=None, agency="spacex", location="florida"):
        with mock.patch.object(self.handler, "_build_v5_data_payload", return_value=payload or PAYLOAD), \
             mock.patch("bot.app.notifications.v6.agency_group", return_value=agency), \
             mock.patch("bot.app.notifications.v6.location_group", return_value=location):
            return self.handler.send_v6_launch_notification(
                launch=mock.MagicMock(), notification_type="oneHour", contents="Launch attempt in one hour."
            )

    def test_webcast_launch_targets_all_six_classes_on_both_platforms(self):
        self._dispatch()
        self.assertEqual(len(_conditions(self.handler.fcm)), 12)

    def test_non_webcast_launch_skips_the_webcast_only_classes(self):
        payload = dict(PAYLOAD, webcast="False")
        self._dispatch(payload=payload)
        conditions = _conditions(self.handler.fcm)
        self.assertEqual(len(conditions), 6)
        self.assertFalse([c for c in conditions if "_w_" in c])

    def test_each_condition_is_emitted_exactly_once(self):
        self._dispatch()
        conditions = _conditions(self.handler.fcm)
        self.assertEqual(len(conditions), len(set(conditions)))

    def test_unmapped_agency_skips_strict_but_keeps_flexible(self):
        self._dispatch(agency=None)
        conditions = _conditions(self.handler.fcm)
        self.assertFalse([c for c in conditions if "_strict" in c])
        self.assertTrue([c for c in conditions if "_flex_" in c])
        self.assertTrue([c for c in conditions if "_all_" in c])

    def test_ios_sends_carry_the_unchanged_apns_config(self):
        self._dispatch()
        ios_calls = [c for c in self.handler.fcm.notify.call_args_list if c.kwargs.get("apns_config")]
        self.assertTrue(ios_calls)
        for call in ios_calls:
            headers = call.kwargs["apns_config"]["headers"]
            self.assertEqual(headers["apns-priority"], "10")
            self.assertEqual(headers["apns-collapse-id"], "uuid-123")
            self.assertEqual(call.kwargs["apns_config"]["payload"]["aps"]["mutable-content"], 1)

    def test_android_sends_are_data_only_with_collapse_key(self):
        self._dispatch()
        android_calls = [c for c in self.handler.fcm.notify.call_args_list if c.kwargs.get("android_config")]
        self.assertTrue(android_calls)
        for call in android_calls:
            self.assertIsNone(call.kwargs["notification_title"])
            self.assertEqual(call.kwargs["android_config"]["collapse_key"], "uuid-123")

    def test_prod_env_appears_in_topic_names_when_debug_is_false(self):
        self._dispatch()
        for condition in _conditions(self.handler.fcm):
            self.assertIn("v6_prod_", condition)

    def test_debug_env_appears_in_topic_names_when_debug_is_true(self):
        self.handler.DEBUG = True
        self._dispatch()
        for condition in _conditions(self.handler.fcm):
            self.assertIn("v6_debug_", condition)

    def test_a_failing_send_does_not_abort_the_remaining_classes(self):
        self.handler.fcm.notify.side_effect = [Exception("boom")] + [None] * 11
        results = self._dispatch()
        self.assertEqual(len(results), 12)
        self.assertEqual(len([r for r in results if r.error is not None]), 1)


class BroadcastDispatchTests(SimpleTestCase):
    def setUp(self):
        self.handler = _Handler()
        self.handler.fcm = mock.MagicMock()
        self.handler.DEBUG = False

    def test_broadcast_emits_one_condition_per_platform(self):
        self.handler.send_v6_broadcast(
            kind="events",
            v5_data={"notification_type": "event_notification", "event_id": "999"},
            title="t",
            body="b",
            collapse_id="event_999",
            category="event",
        )
        conditions = _conditions(self.handler.fcm)
        self.assertEqual(
            sorted(conditions),
            ["'v6_prod_android_events' in topics", "'v6_prod_ios_events' in topics"],
        )
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
docker compose -f docker/docker-compose.test.yml run --rm test \
  python manage.py test bot.tests.test_v6_dispatch --settings=spacelaunchnow.settings.test
```
Expected: FAIL — `ModuleNotFoundError: No module named 'bot.app.notifications.v6'`.

- [ ] **Step 3: Write the implementation**

Create `src/bot/app/notifications/v6.py`:

```python
"""V6 topic-targeted notification dispatch.

Where V5 broadcasts one message per platform and lets the device filter, V6
sends one message per *audience class* with an FCM condition naming the
launch's own attributes. A device subscribes to the type topics of exactly one
class, so at most one condition can match it -- duplicate delivery is
impossible by construction rather than by deduplication.

Payloads and APNs/Android config are identical to V5 on purpose: during the
dual-send window one payload shape ships to two topic schemes.
"""

import logging

from api.models import Launch

from bot.app.notifications.base import NotificationResult
from bot.app.notifications.metrics import record_send, record_skip
from bot.utils.notification_groups import agency_group, location_group
from bot.utils.util import (
    V6_AUDIENCE_CLASSES,
    build_v6_broadcast_condition,
    build_v6_condition,
    v6_class_is_webcast_only,
)

logger = logging.getLogger(__name__)

_PLATFORMS = ("android", "ios")


class V6NotificationMixin:
    """Per-audience-class dispatch. Requires V5NotificationMixin in the MRO for
    ``_build_v5_data_payload`` -- see the module docstring in v5.py."""

    def send_v6_launch_notification(
        self, launch: Launch, notification_type: str, contents: str
    ) -> list[NotificationResult]:
        """Send one message per satisfiable audience class, per platform."""
        data = self._build_v5_data_payload(launch, notification_type, contents)
        env = "debug" if self.DEBUG else "prod"
        has_webcast = data["webcast"] == "True"

        lsp_id = launch.launch_service_provider.id if launch.launch_service_provider else None
        location_id = launch.pad.location.id if launch.pad and launch.pad.location else None
        agency = agency_group(lsp_id)
        location = location_group(location_id)

        results: list[NotificationResult] = []
        for platform in _PLATFORMS:
            for audience_class in V6_AUDIENCE_CLASSES:
                if v6_class_is_webcast_only(audience_class) and not has_webcast:
                    continue
                condition = build_v6_condition(
                    env=env,
                    platform=platform,
                    audience_class=audience_class,
                    notification_type=notification_type,
                    agency_group=agency,
                    location_group=location,
                )
                if condition is None:
                    reason = "unmapped_agency" if agency is None else "unmapped_location"
                    logger.warning(
                        f"V6 skip - class={audience_class} platform={platform} reason={reason} "
                        f"lsp_id={lsp_id} location_id={location_id} launch={launch.id}"
                    )
                    record_skip(platform=platform, audience_class=audience_class, reason=reason)
                    continue
                results.append(
                    self._send_v6(
                        platform=platform,
                        data=data,
                        condition=condition,
                        audience_class=audience_class,
                        title=data["title"],
                        body=data["body"],
                        collapse_id=data["launch_uuid"],
                        category="launch",
                        analytics_label=f"v6_{platform}_{audience_class}_{data['launch_uuid']}",
                    )
                )
        return results

    def send_v6_broadcast(
        self, kind: str, v5_data: dict, title: str, body: str, collapse_id: str, category: str
    ) -> list[NotificationResult]:
        """Send a broadcast type (events / news / announce) to both platforms.

        Broadcasts are not agency/location filtered -- one topic per platform,
        gated by the user's own per-type toggle via their subscription.
        """
        env = "debug" if self.DEBUG else "prod"
        results: list[NotificationResult] = []
        for platform in _PLATFORMS:
            results.append(
                self._send_v6(
                    platform=platform,
                    data=v5_data,
                    condition=build_v6_broadcast_condition(env, platform, kind),
                    audience_class="broadcast",
                    title=title,
                    body=body,
                    collapse_id=collapse_id,
                    category=category,
                    analytics_label=f"v6_{platform}_{kind}_{collapse_id}",
                )
            )
        return results

    def _send_v6(
        self,
        *,
        platform: str,
        data: dict,
        condition: str,
        audience_class: str,
        title: str,
        body: str,
        collapse_id: str,
        category: str,
        analytics_label: str,
    ) -> NotificationResult:
        """One FCM call. Android is data-only; iOS carries the alert."""
        logger.info(f"V6 {platform} [{audience_class}] condition: {condition}")
        kwargs = {
            "data_payload": data,
            "topic_condition": condition,
            "fcm_options": {"analytics_label": analytics_label},
            "timeout": 240,
        }
        if platform == "android":
            kwargs["notification_title"] = None
            kwargs["notification_body"] = None
            kwargs["android_config"] = {
                "priority": "high",
                "collapse_key": collapse_id,
                "ttl": "86400s",
            }
        else:
            kwargs["notification_title"] = title
            kwargs["notification_body"] = body
            kwargs["apns_config"] = {
                "headers": {"apns-priority": "10", "apns-collapse-id": collapse_id},
                "payload": {"aps": {"mutable-content": 1}},
            }

        try:
            result = self.fcm.notify(**kwargs)
            logger.info(f"V6 {platform} [{audience_class}] result: {result}")
            record_send(
                platform=platform, category=category, success=True, result=result,
                audience_class=audience_class,
            )
            return NotificationResult(
                notification_type=data["notification_type"],
                topics=condition,
                result=result,
                analytics_label=analytics_label,
                error=None,
            )
        except Exception as e:
            logger.error(f"V6 {platform} [{audience_class}] error: {e}")
            record_send(
                platform=platform, category=category, success=False, audience_class=audience_class
            )
            return NotificationResult(
                notification_type=data["notification_type"],
                topics=condition,
                result=None,
                analytics_label=analytics_label,
                error=e,
            )
```

- [ ] **Step 4: Run the test to verify it passes**

Run the same command as Step 2. Expected: PASS, 10 tests.

- [ ] **Step 5: Run the full suite**

```bash
docker compose -f docker/docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test
```
Expected: PASS. Nothing dispatches V6 yet.

- [ ] **Step 6: Commit**

```bash
git add src/bot/app/notifications/v6.py src/bot/tests/test_v6_dispatch.py
git commit -m "feat(notifications): add V6 per-audience-class launch dispatch"
```

---

### Task 5: Wire launch dual-send

**Files:**
- Modify: `src/bot/app/notifications/notification_handler.py:14-33` (imports and class bases), `:186-192` (dispatch)
- Test: `src/bot/tests/test_v6_dispatch.py` (add a class)

**Interfaces:**
- Consumes: `V6NotificationMixin.send_v6_launch_notification` (Task 4).
- Produces: nothing new. After this task the server dual-sends every launch notification.

Discord notification keeps receiving the **V5** results only. Changing what Discord reports is out of scope and would make the dual-send window noisy.

- [ ] **Step 1: Write the failing test**

Append to `src/bot/tests/test_v6_dispatch.py`:

```python
class DualSendTests(SimpleTestCase):
    """The V5 broadcast must keep firing alongside V6 for shipped clients."""

    def setUp(self):
        from bot.app.notifications.notification_handler import NotificationHandler

        self.handler = NotificationHandler.__new__(NotificationHandler)
        self.handler.fcm = mock.MagicMock()
        self.handler.DEBUG = False

    def test_v5_broadcast_and_v6_conditions_both_fire(self):
        launch = mock.MagicMock()
        with mock.patch.object(self.handler, "_build_v5_data_payload", return_value=PAYLOAD), \
             mock.patch.object(self.handler, "notify_discord"), \
             mock.patch("bot.app.notifications.v6.agency_group", return_value="spacex"), \
             mock.patch("bot.app.notifications.v6.location_group", return_value="florida"):
            self.handler.send_v3_notification(launch, "oneHour", "Launch attempt in one hour.")

        conditions = _conditions(self.handler.fcm)
        v5 = [c for c in conditions if "prod_v5_" in c]
        v6 = [c for c in conditions if "v6_prod_" in c]
        self.assertEqual(len(v5), 2, "V5 android + ios broadcast must still fire")
        self.assertEqual(len(v6), 12, "V6 must emit 6 classes x 2 platforms for a webcast launch")
```

If `send_v3_notification` builds its own `data` dict from `launch` attributes that a `MagicMock` cannot satisfy (e.g. `launch.net.strftime`), the `MagicMock` returns another mock and the dict still builds — that is fine, the assertions only read `topic_condition`.

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
docker compose -f docker/docker-compose.test.yml run --rm test \
  python manage.py test bot.tests.test_v6_dispatch.DualSendTests --settings=spacelaunchnow.settings.test
```
Expected: FAIL — 0 V6 conditions found (`AssertionError: 0 != 12`).

- [ ] **Step 3: Write the implementation**

In `src/bot/app/notifications/notification_handler.py`, add the import next to the V5 import:

```python
from bot.app.notifications.v5 import V5NotificationMixin
from bot.app.notifications.v6 import V6NotificationMixin
```

Add the mixin to the class bases. The two mixins define disjoint methods, so MRO order carries no behavioural meaning here — list it after `V5NotificationMixin` to keep version order readable:

```python
class NotificationHandler(
    V3NotificationMixin,
    V4NotificationMixin,
    V5NotificationMixin,
    V6NotificationMixin,
    CustomNotificationMixin,
    DiscordNotificationMixin,
    DebugNotificationMixin,
    NotificationService,
):
```

In `send_v3_notification`, add the V6 dispatch immediately after the V5 call and before `notify_discord`:

```python
        # Send v5 notifications with platform-specific messaging
        v5_results = self.send_v5_notification(
            launch=launch,
            notification_type=notification_type,
            contents=contents,
        )

        # Send v6 topic-targeted notifications alongside v5 (dual-send window).
        # v5 serves already-shipped builds; v6 serves upgraded ones, which
        # unsubscribe from the v5 topics. See the V6 design spec.
        self.send_v6_launch_notification(
            launch=launch,
            notification_type=notification_type,
            contents=contents,
        )

        self.notify_discord(v5_results, data)
```

- [ ] **Step 4: Run the test to verify it passes**

Run the same command as Step 2. Expected: PASS.

- [ ] **Step 5: Run the full suite**

```bash
docker compose -f docker/docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test
```
Expected: PASS — including `test_v5_notifications.py` and `test_apns_collapse_id.py`, which must be untouched by this change.

- [ ] **Step 6: Commit**

```bash
git add src/bot/app/notifications/notification_handler.py src/bot/tests/test_v6_dispatch.py
git commit -m "feat(notifications): dual-send V6 launch notifications alongside V5"
```

---

### Task 6: V6 broadcast targeting for events, news, and custom

**Files:**
- Modify: `src/bot/app/events/notification_handler.py:106-168` (end of `_send_v5_event_notification`)
- Modify: `src/bot/app/notifications/news_notification_handler.py` (end of `_send_v5_notification`)
- Modify: `src/bot/app/notifications/custom.py` (end of `_send_v5_custom_ios`)
- Test: `src/bot/tests/test_v6_dispatch.py` (add a class)

**Interfaces:**
- Consumes: `V6NotificationMixin.send_v6_broadcast` (Task 4).
- Produces: nothing new.

Each of the three handlers must gain `V6NotificationMixin` in its bases. For custom notifications the V6 broadcast is sent from the **iOS** method only — `send_v6_broadcast` already covers both platforms, and `check_custom` calls the iOS and Android methods separately, so sending from both would double up.

- [ ] **Step 1: Write the failing test**

Append to `src/bot/tests/test_v6_dispatch.py`:

```python
class BroadcastWiringTests(SimpleTestCase):
    def _v6_conditions(self, fcm_mock):
        return [c for c in _conditions(fcm_mock) if "v6_prod_" in c]

    def test_event_send_also_targets_the_v6_event_topics(self):
        from bot.app.events.notification_handler import EventNotificationHandler

        handler = EventNotificationHandler.__new__(EventNotificationHandler)
        handler.fcm = mock.MagicMock()
        handler.DEBUG = False
        v5 = {"notification_type": "event_notification", "title": "t", "body": "b", "event_id": "999"}
        with mock.patch.object(handler, "_build_v5_event_data", return_value=v5):
            handler._send_v5_event_notification(event=object(), event_type="event")
        self.assertEqual(
            sorted(self._v6_conditions(handler.fcm)),
            ["'v6_prod_android_events' in topics", "'v6_prod_ios_events' in topics"],
        )

    def test_news_send_also_targets_the_v6_news_topics(self):
        from bot.app.notifications.news_notification_handler import NewsNotificationHandler

        handler = NewsNotificationHandler.__new__(NewsNotificationHandler)
        handler.fcm = mock.MagicMock()
        handler.DEBUG = False
        v5 = {"notification_type": "featured_news", "title": "t", "body": "b", "article_id": "777"}
        with mock.patch.object(handler, "_build_v5_news_data", return_value=v5):
            handler._send_v5_notification(article=object())
        self.assertEqual(
            sorted(self._v6_conditions(handler.fcm)),
            ["'v6_prod_android_news' in topics", "'v6_prod_ios_news' in topics"],
        )

    def test_custom_send_also_targets_the_v6_announce_topics(self):
        from bot.app.notifications.custom import CustomNotificationMixin
        from bot.app.notifications.v6 import V6NotificationMixin

        class _Custom(CustomNotificationMixin, V6NotificationMixin):
            pass

        handler = _Custom()
        handler.fcm = mock.MagicMock()
        handler.DEBUG = False
        v5 = {"notification_type": "custom", "title": "t", "body": "b", "custom_id": "cust-1"}
        with mock.patch.object(handler, "_build_v5_custom_data", return_value=v5):
            handler._send_v5_custom_ios(pending=object())
        self.assertEqual(
            sorted(self._v6_conditions(handler.fcm)),
            ["'v6_prod_android_announce' in topics", "'v6_prod_ios_announce' in topics"],
        )
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
docker compose -f docker/docker-compose.test.yml run --rm test \
  python manage.py test bot.tests.test_v6_dispatch.BroadcastWiringTests --settings=spacelaunchnow.settings.test
```
Expected: FAIL — `AttributeError: 'EventNotificationHandler' object has no attribute 'send_v6_broadcast'`.

- [ ] **Step 3a: Wire events**

In `src/bot/app/events/notification_handler.py`, add the import and mixin:

```python
from bot.app.notifications.v6 import V6NotificationMixin
```

Add `V6NotificationMixin` to the `EventNotificationHandler` class bases. Then append to the end of `_send_v5_event_notification`, after the iOS block:

```python
        # V6 topic-targeted broadcast (dual-send window)
        self.send_v6_broadcast(
            kind="events",
            v5_data=v5_data,
            title=v5_data["title"],
            body=v5_data["body"],
            collapse_id=f"event_{v5_data['event_id']}",
            category="event",
        )
```

- [ ] **Step 3b: Wire news**

In `src/bot/app/notifications/news_notification_handler.py`, add the same import, add `V6NotificationMixin` to the `NewsNotificationHandler` bases, and append to the end of `_send_v5_notification`:

```python
        # V6 topic-targeted broadcast (dual-send window)
        self.send_v6_broadcast(
            kind="news",
            v5_data=v5_data,
            title=v5_data["title"],
            body=v5_data["body"],
            collapse_id=f"news_{v5_data['article_id']}",
            category="news",
        )
```

- [ ] **Step 3c: Wire custom**

In `src/bot/app/notifications/custom.py`, add the same import. `CustomNotificationMixin` is composed into `NotificationHandler`, which already gains `V6NotificationMixin` in Task 5, so no base change is needed there — but append to the end of `_send_v5_custom_ios`:

```python
        # V6 topic-targeted broadcast (dual-send window). Sent from the iOS
        # method only: send_v6_broadcast covers both platforms, and check_custom
        # invokes the iOS and Android methods separately.
        self.send_v6_broadcast(
            kind="announce",
            v5_data=v5_data,
            title=v5_data["title"],
            body=v5_data["body"],
            collapse_id=f"custom_{v5_data['custom_id']}",
            category="custom",
        )
```

- [ ] **Step 4: Run the test to verify it passes**

Run the same command as Step 2. Expected: PASS, 3 tests.

- [ ] **Step 5: Run the full suite**

```bash
docker compose -f docker/docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test
```
Expected: PASS — `test_apns_collapse_id.py` in particular must still pass, since its helper selects the *first* call with `apns_config` and the V5 iOS send still precedes the V6 ones.

- [ ] **Step 6: Commit**

```bash
git add src/bot/app/events/notification_handler.py src/bot/app/notifications/news_notification_handler.py src/bot/app/notifications/custom.py src/bot/tests/test_v6_dispatch.py
git commit -m "feat(notifications): dual-send V6 broadcasts for events news and custom"
```

---

### Task 7: Update the delivery documentation

**Files:**
- Modify: `docs/superpowers/specs/2026-05-25-v5-only-notification-delivery-matrix.md` (header note + a V6 section)
- Modify: `docs/superpowers/specs/2026-08-13-v6-topic-targeted-notifications-design.md` (status line)

No test — documentation only. The delivery matrix is the document a future reader consults to learn how notifications reach users, and it currently states that all filtering is client-side. Leaving it stale is how the next person repeats this investigation.

- [ ] **Step 1: Add a revision note to the delivery matrix**

Insert immediately after the existing `> **Revision 2026-05-26.**` block:

```markdown
> **Revision 2026-08-13 — V6 topic targeting.** The server now **dual-sends**: the V5 broadcast
> described below still goes to `prod_v5_ios` / `prod_v5_android` for already-shipped builds, and
> a parallel V6 path targets upgraded clients by FCM topic condition. On the V6 path **no
> filtering happens on the device** — agency, location, matching mode, per-type toggles, webcast-only
> and the broadcast toggles are all resolved server-side at send time. The client-side filtering
> documented below therefore describes the V5 path only. See
> `2026-08-13-v6-topic-targeted-notifications-design.md`. The "Remaining gaps" section at the
> bottom is resolved on the V6 path: per-type filtering is enforced by the type topic, and the
> foreground/NSE divergence cannot occur because neither path filters.
```

- [ ] **Step 2: Update the V6 spec status**

In `docs/superpowers/specs/2026-08-13-v6-topic-targeted-notifications-design.md`, change:

```markdown
**Status:** Draft — awaiting review
```

to:

```markdown
**Status:** Server implemented (dual-send live, no clients subscribed yet) — client pending
```

- [ ] **Step 3: Verify the docs render and links resolve**

Run:
```bash
grep -n "2026-08-13-v6-topic-targeted-notifications-design.md" docs/superpowers/specs/*.md
ls docs/superpowers/specs/2026-08-13-v6-topic-targeted-notifications-design.md
```
Expected: the cross-reference is found and the target file exists.

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/2026-05-25-v5-only-notification-delivery-matrix.md docs/superpowers/specs/2026-08-13-v6-topic-targeted-notifications-design.md
git commit -m "docs(notifications): record V6 dual-send in the delivery matrix"
```

---

## After This Plan

The server is now dual-sending. **This is a production no-op until clients subscribe** — no device is subscribed to any `v6_*` topic, so every V6 condition matches zero devices. That is the intended state and makes steps 1-6 independently revertable.

Two things remain, neither in this plan:

1. **The KMP client plan** — subscription derivation, preference migration from IDs to group names, the `otherAgency` settings row, and the NSE teardown. Per the companion spec the server must be live first, which this plan satisfies.
2. **Retirement** — deleting `v5.py`, the V5 send sites, and the `prod_v5_*` broadcasts once V6-capable builds pass the adoption threshold. A separate PR, deliberately not bundled.

**Verification note:** every test in this plan proves that the *right conditions are constructed*. None of them prove *delivery*. The acceptance gate for the whole effort is the on-device matrix in the spec — especially the iOS force-quit cases, which are what is broken today and what no unit test can reach.

**Assumption carried from the spec review:** the group tables include `otherAgency`, which requires a new "Other Agencies" settings row in the KMP app. This was recommended and not explicitly signed off. If it is declined, remove `DEFAULT_AGENCY_GROUP`'s catch-all behaviour in Task 1 (return `None` for unknown IDs instead), update `EXPECTED_AGENCY_GROUP_NAMES`, and the existing strict-skip path in Task 4 handles the rest unchanged.
