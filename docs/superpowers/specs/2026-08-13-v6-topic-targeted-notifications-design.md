# V6 Topic-Targeted Notification Delivery — Server

**Date:** 2026-08-13
**Status:** Draft — awaiting review
**Repo:** SpaceLaunchNow-Server
**Companion spec (client):** `SpaceLaunchNow-KMP-Main/docs/superpowers/specs/2026-08-13-v6-topic-targeted-notifications-kmp-design.md`

This document is the **authoritative topic contract**. The KMP companion spec describes the client
subscription, preference migration, and NSE changes; where the two disagree, this one wins.

## Problem

Under V5 the server broadcasts every launch notification to a single topic per platform
(`prod_v5_ios` / `prod_v5_android`, `v5.py:170-185`) and **all** per-user filtering happens on the
device. On iOS that filtering runs in a Notification Service Extension that suppresses unwanted
pushes by blanking their content.

That makes the correctness of a user's notification set depend on an extension that must be
scheduled, must read fresh App Group state, and must finish inside the APNs time budget. When any
of those fails, the failure is **silent and total, in both directions**:

- A customer on 5.31.2-b75 with strict matching and TX/FL selected receives *every* launch,
  including Zhuque-2E from Jiuquan — a launch no filter mode would admit.
- Background/killed-app notifications are currently **not arriving at all** for affected users,
  which is the fail-closed side of the same coin: stale or missing App Group keys make the NSE
  suppress everything.

Two further defects are structural rather than incidental:

- `V5NotificationFilter` still carries a `// TODO` for per-type checks, so the killed-app path does
  not honour the 24h/1h/10min toggles at all, and can disagree with the foreground path
  (`2026-05-25-v5-only-notification-delivery-matrix.md`, Remaining gaps 1–2).
- Agency and location groupings (`additionalIds`) live in the shipped app, so a newly added launch
  site or agency ID is invisible to every filtered user until an app release reaches their device.

No amount of hardening inside the NSE removes the underlying property: **the device cannot be the
thing that decides whether a push it already received should have been sent.**

## Approach

Move all per-user filtering to FCM topic conditions evaluated at send time. The device's
*subscription set* performs the match; the condition merely names the launch's own attributes. A
device receives only what it should display, so the NSE has nothing left to suppress and becomes
enrichment-only and fail-open.

Both platforms move. iOS and Android share one topic scheme.

### Reversal of a prior decision

In July 2026 topic-condition targeting was rejected because multi-topic conditions had historically
caused silent non-delivery. That failure mode is real: FCM permits **at most five topics per
condition** and degrades rather than erroring when a condition is malformed or over-budget.

This design treats that ceiling as a hard, tested constraint rather than an incidental detail:

- Every condition this design emits contains **at most three** topics, by construction.
- Conditions are generated from a single class table, not hand-written per call site.
- A unit test asserts the topic count of every generated condition, so a future dimension cannot
  quietly push a condition over budget.

The margin between the 3-topic design and the 5-topic ceiling is deliberate: it leaves room for one
future dimension without redesigning the scheme.

## Topic namespace

Two kinds of topic. Names are chosen to be readable in logs and typable in the FCM console.

### Attribute topics — shared across platforms

```
v6_<env>_<group>          e.g. v6_prod_spacex, v6_prod_florida, v6_debug_china
```

`env` ∈ `{prod, debug}`. `group` is one of the group names the app offers — 22 today (11 agencies,
11 locations), 23 with the `otherAgency` row proposed below. These are **not** platform-scoped: the
platform is carried by the type topic, so a device subscribes to each attribute once.

### Type topics — platform-, class-, and type-scoped

```
v6_<env>_<platform>_<class>_<type>    e.g. v6_prod_ios_flex_oneHour
                                           v6_prod_android_strict_w_tenMinutes
```

`platform` ∈ `{ios, android}` (payload shape differs: iOS alert + `mutable-content`, Android
data-only). `class` is the audience class (below). `type` is the existing `notification_type`
string.

### Broadcast topics

```
v6_<env>_<platform>_<kind>            e.g. v6_prod_ios_events
                                           v6_prod_android_news
                                           v6_prod_ios_announce
```

> **Naming note.** The sketch this design came from mixed env placement
> (`v6i_t_oneHour` alongside `v6_prod_florida`). Normalised so every topic reads
> `v6_<env>_…` left to right; these strings are read in logs and pasted into the FCM console, and
> the abbreviation saves nothing that matters.

## Audience classes

A device belongs to exactly one class, determined by its `followAllLaunches`, `useStrictMatching`,
and `webcastOnly` settings. The class is encoded in the **type** topic — not the attribute topic —
so attribute topics stay single-copy and shared, and flipping strict mode resubscribes ≤11 type
topics instead of every agency and location the user follows.

| Class      | Device settings                              | Condition emitted                                                    | Topics |
|------------|----------------------------------------------|----------------------------------------------------------------------|--------|
| `all`      | `followAllLaunches`                          | `'…_all_<type>' in topics`                                            | 1 |
| `flex`     | not follow-all, not strict                   | `'…_flex_<type>' in topics && ('<lsp>' in topics \|\| '<loc>' in topics)` | 3 |
| `strict`   | not follow-all, strict                       | `'…_strict_<type>' in topics && '<lsp>' in topics && '<loc>' in topics`  | 3 |
| `all_w`    | as `all`, plus `webcastOnly`                 | same shape as `all`                                                   | 1 |
| `flex_w`   | as `flex`, plus `webcastOnly`                | same shape as `flex`                                                  | 3 |
| `strict_w` | as `strict`, plus `webcastOnly`              | same shape as `strict`                                                | 3 |

Worked example — `oneHour` for a SpaceX launch from Florida, iOS, prod:

```
all      'v6_prod_ios_all_oneHour' in topics
flex     'v6_prod_ios_flex_oneHour' in topics
         && ('v6_prod_spacex' in topics || 'v6_prod_florida' in topics)
strict   'v6_prod_ios_strict_oneHour' in topics
         && 'v6_prod_spacex' in topics && 'v6_prod_florida' in topics
```

### Why duplicates are structurally impossible

A device subscribes to type topics of **exactly one** class (the client derives the class from its
settings and unsubscribes the others). Every condition is anchored on a class-specific type topic.
Therefore at most one condition per launch notification per platform can match any given device —
regardless of how many attribute topics that device is subscribed to.

This is the property the naive form of the scheme loses: if both the strict and flexible conditions
referenced the same mode-agnostic attribute topics, a device following SpaceX *and* Florida would
match both and receive two pushes for every launch. Encoding the mode somewhere is not optional,
and the type topic is the cheapest place to put it.

Note this is a property of the *scheme*, not of runtime deduplication — no collapse-id or
downstream merge is doing the work.

## Send matrix

Per launch notification, per platform:

| Launch | Classes targeted |
|---|---|
| No webcast | `all`, `flex`, `strict` |
| Has webcast | `all`, `flex`, `strict`, `all_w`, `flex_w`, `strict_w` |

Maximum 12 FCM calls per launch notification across both platforms (6 without a webcast), up from
2 today. At current volume — order 10³–10⁴ notification events per year — this is immaterial. The
sends are generated by iterating a class table, not by twelve code paths.

Broadcast notifications (event / news / custom) are one condition per platform, unchanged in count.

### Skip rules

A send is **skipped**, not emitted with a missing term, when its condition cannot be satisfied:

- `strict` / `strict_w` when the launch's agency or location has no group — the condition would be
  unsatisfiable, since no user's selection can match an ungrouped attribute.
- `flex` / `flex_w` when *neither* attribute has a group — degrades to a single-term condition when
  exactly one has a group (this is the common and correct case: a LandSpace launch from Jiuquan has
  no agency group but does map to `v6_prod_china`, and a China-following user must still receive
  it).
- Any class whose `<type>` is not a real notification type.

With a total group table (below) the strict skip cannot occur in practice. The guard stays anyway:
it is the difference between "nobody receives this" and "a malformed condition is sent to FCM".

## The group table

The server owns the mapping from raw LL2 IDs to group names; the app owns only the list of group
*names* it offers.

This split is the reason attribute topics use names (`v6_prod_china`) rather than raw IDs
(`v6_prod_loc_17`). With raw IDs the `additionalIds` groupings stay frozen in the shipped app, and
a new launch site is invisible to filtered users until an app release propagates. With names, a new
pad ID is added to the server table and starts matching for **already-installed clients** on the
next deploy.

### Location

Initial contents mirror `NotificationLocation` in the KMP app exactly:

| Group | LL2 location IDs |
|---|---|
| `van` | 11 |
| `florida` | 27, 12 |
| `wallops` | 21, 1, 25, 31, 155, 162 |
| `texas` | 143, 29 |
| `russia` | 15, 5, 6, 18, 30, 146 |
| `frenchGuiana` | 13 |
| `newZealand` | 10 |
| `japan` | 24, 26, 32, 166 |
| `isro` | 14 |
| `china` | 17, 8, 16, 19 |
| `other` | 20, 3, 144 — **and every location ID not listed above** |

### Agency

| Group | LL2 agency IDs |
|---|---|
| `spacex` | 121 |
| `nasa` | 44 |
| `blueOrigin` | 141 |
| `rocketLab` | 147 |
| `virginGalactic` | 1024 |
| `ula` | 124 |
| `arianespace` | 115 |
| `roscosmos` | 111, 96, 193, 63 |
| `northrop` | 257 |
| `casc` | 88, 194 |
| `isroAgency` | 31 |
| `otherAgency` | **every agency ID not listed above** |

### Totality, and the one product decision this requires

Both tables are **total**: every ID maps to exactly one group, with `other` / `otherAgency`
absorbing the long tail. Totality is what removes the strict-skip case and guarantees every launch
is reachable by some filtered user rather than only by follow-all subscribers.

`other` already exists as a user-facing location ("Misc. (Sea, Air, etc)"). **`otherAgency` does
not exist today and requires a new settings row** ("Other Agencies") in the KMP app. Recommended,
because without it a LandSpace or Firefly launch remains unreachable for strict users no matter
what they select. **This needs sign-off** — it is the only user-visible product change in the
design. If declined, the strict skip rule stays live for ungrouped agencies and this spec is
otherwise unaffected.

`isro` appears as both a location group (ID 14) and an agency group (ID 31) in the current app
model, under the same `topicName`. Since attribute topics are a single flat namespace, the agency
group is renamed `isroAgency` to disambiguate. Location `isro` is left alone to avoid churning a
name users are already subscribed to under V5's sibling scheme.

### Implementation

A module-level constant in `src/bot/utils/notification_groups.py`:

```python
LOCATION_GROUPS: dict[int, str] = {11: "van", 27: "florida", 12: "florida", ...}
AGENCY_GROUPS: dict[int, str] = {121: "spacex", 44: "nasa", ...}

DEFAULT_LOCATION_GROUP = "other"
DEFAULT_AGENCY_GROUP = "otherAgency"

def location_group(location_id: int | None) -> str | None: ...
def agency_group(agency_id: int | None) -> str | None: ...
```

Code constant rather than a DB model: it is reviewable, versioned with the conditions that consume
it, and needs no migration. A deploy is minutes against an app release's days-plus-adoption-lag, so
the "update without an app release" benefit is fully realised. Promote to a DB table later if the
edit frequency ever justifies it.

The inverse map (group name → IDs) is **not** needed server-side and must not be built; the client
never sends IDs to the server.

## Files changed

| File | Change |
|---|---|
| `src/bot/utils/notification_groups.py` | **New.** Group tables + lookup helpers. |
| `src/bot/utils/util.py` | Add `build_v6_condition(...)`, `get_v6_type_topic(...)`, `get_v6_broadcast_topic(...)`. V3 helpers left untouched and uninvoked. |
| `src/bot/app/notifications/v6.py` | **New.** `V6NotificationMixin` — class table, per-class dispatch, skip rules. |
| `src/bot/app/notifications/notification_handler.py` | Compose `V6NotificationMixin`; launch sends go through V6 plus the V5 dual-send. |
| `src/bot/app/events/notification_handler.py` | Broadcast event sends target `v6_<env>_<platform>_events` alongside the V5 topic. |
| `src/bot/app/notifications/news_notification_handler.py` | Same, `…_news`. |
| `src/bot/app/notifications/custom.py` | Same, `…_announce`. |
| `src/bot/app/notifications/metrics.py` | Add an `audience_class` label to `NOTIFICATIONS_SENT`. |

`v5.py` is retained and still invoked for the dual-send window; it is deleted at retirement, not
now.

### Condition builder

```python
def build_v6_condition(
    *, env: str, platform: str, audience_class: str, notification_type: str,
    agency_group: str | None, location_group: str | None,
) -> str | None:
    """Return an FCM condition, or None when the class cannot be satisfied."""
```

Returns `None` for the skip cases above. Every return value contains ≤3 topics — asserted by test,
not by convention.

## Payload

**Unchanged.** The flat V5 data payload is kept verbatim, including `lsp_id` / `location_id` /
`program_id` and the display fields — clients still need them for rendering and deep-linking, and
keeping the payload stable means the dual-send window ships one payload shape to two topic schemes.

Also unchanged: `apns-collapse-id` (per `2026-06-20-ios-apns-collapse-id-design.md`),
`mutable-content: 1`, `apns-priority: 10`, Android `collapse_key` / `priority: high` / `ttl`.

`mutable-content` stays because the NSE survives as an enrichment step (image attachment, re-alert
policy). It is now **fail-open**: if the NSE crashes, times out, or reads stale state, iOS renders
the original alert instead of swallowing it. See the KMP companion spec.

## Broadcast types

Event, news, and custom notifications become one-topic conditions per platform
(`'v6_prod_ios_events' in topics`). The per-type toggle moves from a client-side check reading
App Group keys (`nse_topic_events` / `nse_topic_featured_news` / `nse_topic_announcements`) to a
subscription decision, and those App Group keys are retired.

## Dual-send window

The server sends **both** schemes during migration:

- **V5 broadcast** to `prod_v5_ios` / `prod_v5_android` — serves already-shipped builds, which keep
  their current client-side filtering behaviour, unchanged and un-regressed.
- **V6 conditions** — serve upgraded builds.

Upgraded clients unsubscribe from the V5 topics as part of their subscription reconciliation, so a
device receives from exactly one scheme. The transitional risk is a device that has upgraded but
whose unsubscribe call has not yet succeeded: it briefly receives both, which `apns-collapse-id` /
`collapse_key` collapse to one visible notification, at the cost of one extra alert. Subscription
reconciliation re-runs on every app start, so this converges.

**Retirement criteria** — remove the V5 broadcast and delete `v5.py` when both hold:

1. V6-capable builds exceed an adoption threshold to be chosen at rollout time (recommend ≥95% of
   30-day-active installs).
2. The V6 path has run one full release cycle without a delivery regression report.

Retirement is a separate PR, deliberately not bundled with the cutover.

## Observability

Topic-condition sends return `{"name": "projects/.../messages/..."}` with **no per-device or
per-recipient count** — `metrics.py:53-65` already documents this. This design therefore improves
*correctness* without improving *delivery observability*, and that limitation is inherent to topic
messaging rather than to this scheme.

What is gained:

- `sln_notifications_sent_total` gains an `audience_class` label, so per-class send volume, skip
  rates, and per-class failures are visible.
- Skipped sends are logged with the reason and the unmapped ID, which surfaces gaps in the group
  table as data rather than as user reports.

What is still not answerable: "did *this specific device* receive it?" A per-device token registry
with `send_each` (July's Option C) is the only thing that answers that. This design does not
foreclose it — a registry would replace the send layer while leaving the group table and the
settings model intact — but it is explicitly **out of scope**.

## Testing

**Unit — the condition builder is the whole risk surface:**

1. Every generated condition contains ≤3 topics. Parameterised across all 6 classes × all
   notification types × mapped/unmapped attribute combinations. This is the regression guard for
   the failure that caused the July rejection.
2. Conditions are syntactically well-formed: balanced parens, `in topics` on every term.
3. Class disjointness: for a given launch and platform, no two class conditions can be satisfied by
   one subscription set. Assert by enumerating the class type-topics and checking pairwise
   exclusivity.
4. Skip rules return `None` for unsatisfiable strict and fully-unmapped flexible.
5. Group lookup is total: every agency/location ID resolves to a group, including unknown IDs
   falling to `otherAgency` / `other`.
6. Group-name set pinned against an explicit literal transcribed from this spec, so an accidental
   server-side rename or removal fails CI. Note the limit honestly: a server test cannot read the
   KMP repo, so this catches server-side drift only. The client pins the *same* literal on its
   side, which makes a divergence fail in one repo or the other — but genuine cross-repo parity
   remains a review checklist item, not an automated gate.

**Integration:** run the notification tracker against a fixture launch with a stubbed `self.fcm`;
assert the exact set of conditions emitted for webcast and non-webcast launches, and that the V5
broadcast still fires alongside.

**Staging:** `v6_debug_*` topics against debug builds, covering each class end to end.

**Device (the gate — none of the above proves delivery):**

| Case | Expected |
|---|---|
| Flexible user, matching agency, app force-quit | Notification arrives and renders |
| Flexible user, non-matching launch | Nothing arrives at all (verify at the FCM/device level, not by absence of a banner) |
| Strict user, agency matches but location does not | Nothing arrives |
| Follow-all user | Every launch arrives |
| Disabled type toggle | Nothing arrives for that type |
| `webcastOnly` user, launch without webcast | Nothing arrives |
| NSE deliberately made to fail | Notification still renders, unenriched — proves fail-open |
| Both platforms | Behaviour identical |

The force-quit cases are the ones that matter: they are what is broken today, and they are exactly
what unit tests cannot reach.

## Rollout

1. Group table + condition builder + tests. No behaviour change; nothing dispatches yet.
2. V6 dispatch added alongside V5. Server now dual-sends; no client subscribes to V6 yet, so this
   is a no-op in production and safely verifiable in isolation.
3. KMP client ships subscription + NSE changes (companion spec). Staged release.
4. Device verification matrix on both platforms.
5. Retirement PR once the criteria above are met.

Steps 1–2 are server-only and independently revertable. The server is never in a state where V5
delivery depends on V6 being correct.

## Risks

| Risk | Mitigation |
|---|---|
| A condition exceeds the FCM ceiling and silently under-delivers — the failure that caused the July rejection | ≤3 by construction, asserted by test on every generated condition; 2 topics of headroom |
| Group table drifts from the app's group names | Each repo pins the name set against the same literal, so a one-sided edit fails that repo's CI. Only the 22 names must agree — the server owns IDs, the app owns names — but cross-repo parity is a review check, not an automated gate |
| A client's subscribe call fails, silently reducing what a user receives | Client-side concern — reconciliation, retry, and a Diagnostics surface are specified in the companion spec. **This is the primary new failure mode this design introduces** and it is why the companion spec is not optional |
| Double delivery during the dual-send window | Collapse-id merges the visible notification; reconciliation converges; time-boxed by retirement criteria |
| A new notification dimension pushes conditions over budget later | Headroom of 2 topics, plus the count test forces the trade-off to be made explicitly |

## Non-goals

- Per-device token registry / `send_each` (July's Option C) — deferred, not foreclosed.
- Changing Android's data-only rendering path.
- V3 / V4 / Flutter senders — remain retained and uninvoked.
- Payload shape, deep-linking, notification history.
- `hideTbdLaunches` — persisted in `NotificationState` but read by no notification filter path in
  either client; it is a list-display setting and is deliberately not given a topic dimension.
