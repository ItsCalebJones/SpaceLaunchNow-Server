# iOS Notification Collapse via `apns-collapse-id` — Server

**Date:** 2026-06-20
**Status:** Draft
**Repo:** SpaceLaunchNow-Server
**Companion spec (client):** `SpaceLaunchNow-KMP-Main/docs/superpowers/specs/2026-06-20-ios-notification-realert-policy-design.md`
— iOS phase-aware re-alert policy (NSE + AppDelegate sound/interruption). **Not required for this
spec to ship**; the two are independent and can land in either order.

## Problem

iOS notifications do not collapse. When a launch progresses through its lifecycle
(`twentyFourHour` → `oneHour` → `tenMinutes` → `oneMinute` → `inFlight` → `success`), each push
is rendered by the system as a **separate** notification, so a single launch stacks up to half a
dozen entries in Notification Center. Android does not have this problem: the V5 Android push
already sets `collapse_key`, and the Android client re-uses one notification tag per launch, so a
launch shows exactly one always-current notification.

The reliable iOS delivery path when the app is backgrounded or killed is the Notification Service
Extension (NSE), where **the system renders the notification** and the NSE can only mutate
content — it cannot change the notification's request identifier. Therefore the **only** lever
that collapses iOS notifications on that path is the APNs
[`apns-collapse-id`](https://developer.apple.com/documentation/usernotifications/setting_up_a_remote_notification_server/sending_notification_requests_to_apns)
header, which is set server-side. APNs replaces any visible notification sharing the same
collapse-id with the newest one.

Today none of the V5 iOS send sites set this header.

## Approach

Add an `apns-collapse-id` header to every V5 iOS push, keyed to the entity the notification is
about. The required key **already exists** at each send site as the value passed to the V5
**Android** `collapse_key` — we mirror that same string into the iOS `apns_config["headers"]`.
No new fields, no payload changes, no new files.

This brings iOS to parity with the collapse behavior Android already has, on the only path that
works when the app is killed.

## Collapse-id contract

| Type   | Entity key (value)              | Source today (Android `collapse_key`)                                  |
|--------|---------------------------------|------------------------------------------------------------------------|
| Launch | `<launch_uuid>`                 | `data["launch_uuid"]` — `v5.py:122`                                     |
| Event  | `event_<event_id>`              | `f"event_{v5_data['event_id']}"` — `events/notification_handler.py:124` |
| News   | `news_<article_id>`             | `f"news_{v5_data['article_id']}"` — `news_notification_handler.py:59`   |
| Custom | `custom_<custom_id>`            | `f"custom_{v5_data['custom_id']}"` — `custom.py:83`                     |

The launch key is the bare UUID (matches the Android `collapse_key`, and matches the identifier
the iOS client already uses on its local-reschedule path, `AppDelegate.scheduleNotification`).
The broadcast keys keep the `event_` / `news_` / `custom_` prefixes already used for the Android
`collapse_key` and the iOS client notification tags, so collapse semantics are identical across
platforms.

### Constraint: ≤ 64 bytes

APNs requires `apns-collapse-id` to be at most 64 bytes. All four keys satisfy this with wide
margin: a UUID is 36 chars; the prefixed integer-id keys are well under 20. No truncation or
hashing is needed. If a future entity key could exceed 64 bytes, hash it; none can today.

## Architecture

### Files changed

All four changes are identical in shape: add one key to the existing
`apns_config["headers"]` dict (which already contains `apns-priority`). `pyfcm`'s
`FCMNotification.notify` forwards `apns_config["headers"]` to APNs verbatim (proven by the
existing `apns-priority` header), so no wrapper changes are needed.

**1. `src/bot/app/notifications/v5.py`** — `send_notif_v5_ios` (launch).

The method receives `data` but not an explicit key, so read `data["launch_uuid"]` (already
present in the payload, used as the Android `collapse_key` at line 122):

```python
apns_config={
    "headers": {
        "apns-priority": "10",
        "apns-collapse-id": data["launch_uuid"],   # ← add
    },
    "payload": {
        "aps": {
            "mutable-content": 1,
        },
    },
},
```

**2. `src/bot/app/events/notification_handler.py`** — V5 iOS event send (~line 147).

```python
apns_config={
    "headers": {
        "apns-priority": "10",
        "apns-collapse-id": f"event_{v5_data['event_id']}",   # ← add
    },
    "payload": {"aps": {"mutable-content": 1}},
},
```

**3. `src/bot/app/notifications/news_notification_handler.py`** — V5 iOS news send (~line 82).

```python
apns_config={
    "headers": {
        "apns-priority": "10",
        "apns-collapse-id": f"news_{v5_data['article_id']}",   # ← add
    },
    "payload": {"aps": {"mutable-content": 1}},
},
```

**4. `src/bot/app/notifications/custom.py`** — V5 iOS custom send (~line 108).

```python
apns_config={
    "headers": {
        "apns-priority": "10",
        "apns-collapse-id": f"custom_{v5_data['custom_id']}",   # ← add
    },
    "payload": {"aps": {"mutable-content": 1}},
},
```

### What does NOT change

- **Android** — already collapses via `collapse_key`. Untouched.
- **Payloads** — no data fields added or renamed. The keys are derived from values already in the
  payload.
- **Topics, priority, mutable-content, TTL** — unchanged.
- **V3 / V4 / Flutter senders** — out of scope (the KMP app is V5-only).
- **`fcm.notify` wrapper / `NotificationService`** — no signature or passthrough change.

## Interaction with the client re-alert policy (cross-reference, not in scope here)

The companion KMP spec makes the iOS client decide *whether to play sound* per
`notification_type` (re-alert only for the high-value phases — `oneMinute`, `inFlight` (liftoff),
and `success`; whether `failure`/`partialFailure` also re-alert is decided in that spec — with
reminders/webcast/schedule changes updating silently). That decision is made
entirely client-side in the NSE and AppDelegate by reading `notification_type`, which is already
in every payload. **This server spec has no dependency on it and creates no dependency for it.**
`apns-collapse-id` controls *which notification is replaced*; the client controls *whether the
replacement buzzes*. The two are orthogonal and can ship in either order. Shipping this spec
first yields collapse with the current always-buzz behavior; shipping the client spec first
changes buzz behavior without yet collapsing.

## Testing & verification

Collapse cannot be unit-tested meaningfully (it is APNs runtime behavior), so verification is
device-based plus a light assertion that the header is emitted.

1. **Header emission (automated, cheap).** If/where these senders have unit coverage, assert the
   constructed `apns_config["headers"]` contains `apns-collapse-id` with the expected value for
   each type. Otherwise add a focused test that calls the send method with a stubbed `self.fcm`
   and inspects the `apns_config` kwarg.
2. **Device — launch lifecycle (killed app).** Trigger two notifications for the same launch
   (e.g. `oneHour` then `tenMinutes`) with the app **force-quit**. Expected: one notification in
   Notification Center, showing the latest phase, not two.
3. **Device — foreground.** Repeat with the app foregrounded. Expected: the banner updates in
   place rather than stacking.
4. **Device — distinct launches don't collapse.** Two different launches must remain two
   notifications (guards against an accidentally-shared key).
5. **Broadcasts.** Resend the same custom/news/event notification twice; expected single entry.

Debug send paths (`bot/app/notifications/debug.py`, the in-app iOS test helpers) are convenient
triggers for steps 2–5.

## Risks & mitigations

- **Wrong/over-broad key → unrelated notifications collapse into one.** Mitigated by reusing the
  exact per-entity keys already validated for the Android `collapse_key`, and by verification
  step 4.
- **Key > 64 bytes → APNs rejects the push.** Not possible with current keys (see constraint);
  documented so future entity types are checked.
- **Always-buzz on collapse until the client spec lands.** Accepted and expected — collapse is a
  strict UX improvement over stacking even while every phase still alerts. The re-alert policy is
  a separate, additive client change.

## Non-goals

- Changing Android behavior.
- The iOS client re-alert / sound / interruption-level policy (companion KMP spec).
- Reworking delivery topology, filtering, history, or deep-linking.
- V3/V4/Flutter notification paths.

## Rollout

Single PR; four one-line additions. No migration, no payload/version bump, no client release
required for the collapse to take effect (the header acts on the system-rendered notification on
existing app versions). Ship and verify on a real device with the app force-quit.
