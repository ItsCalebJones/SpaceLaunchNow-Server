# V5-Only Notification Delivery Matrix

**Date:** 2026-05-25 (revised 2026-05-26)
**Status:** Documented (reflects implemented state)

## Problem

The server dispatches **only V5 notifications** — all V3 (all/strict/not-strict/flutter) and V4
paths are retained in code but no longer invoked. For each notification *type*, does the V5
message reach the KMP app, and does the app *display* it? "Sent" is not "shown" — the KMP app
applies client-side filtering and each type needs a parser, channel, and display handler.

This document records the end-to-end state: **server dispatch → KMP receipt → KMP display**,
per type, per platform.

> **Revision 2026-05-26.** The earlier version documented news and custom as *dark* (no V5
> path) and events as kill-switch-only. Both have since been implemented, and the filtering
> model corrected. Changes captured here:
> - **News** and **Custom** now have full V5 paths (server send + KMP parse/display/tap).
> - Broadcast types (event/news/custom) are now gated by **their own per-type toggle**
>   (`EVENTS` / `FEATURED_NEWS` / `ANNOUNCEMENTS`) plus the global kill switch — *not* just the
>   kill switch. The previously-ignored **`EVENTS` toggle bug is fixed**.
> - **iOS foreground** now shows banners for all three broadcast types (toggle-gated);
>   previously events were suppressed in the foreground.
> - **iOS event deep-linking** is now actually wired (`setNotificationEventId`); it was
>   aspirational in the prior version.
>
> Verification note: Android/server changes are compiled + runner-tested; **iOS (Swift) is
> code-review-verified only** (no Xcode/Windows) and awaits a Mac/Xcode compile + device pass.

## Server dispatch state

| Handler | V3 | V4 | V5 | Net effect |
|---|---|---|---|---|
| Launch (`notification_handler.py`) | disabled | disabled | **sent** | V5 only |
| Event (`events/notification_handler.py`) | disabled | n/a | **sent** | V5 only |
| News (`news_notification_handler.py`) | disabled | n/a | **sent** | V5 only (`send_notification` → `_send_v5_notification`; re-enabled in `event_tracker.check_news_item`) |
| Custom admin (`custom.py` via `check_custom`) | disabled | n/a | **sent** | V5 only (`_send_v5_custom_ios` / `_send_v5_custom_android`; `check_custom` two-loop dispatch) |

All four types now dispatch on V5. Non-V5 methods are retained, uninvoked.

## KMP subscription

The KMP app subscribes only to V5 topics and actively unsubscribes from legacy V4 topics.

| Platform | Topic (prod) | Topic (debug) |
|---|---|---|
| V5 Android | `prod_v5_android` | `debug_v5_android` |
| V5 iOS | `prod_v5_ios` | `debug_v5_ios` |

Source: `composeApp/src/commonMain/kotlin/.../data/repository/SubscriptionProcessor.kt:143-167`.
Android V5 messages are **data-only** (the app builds the system notification); iOS V5 messages
are **alert + `mutable-content=1`** processed by a Notification Service Extension (NSE).

## Delivery matrix: sent → received → shown

Legend: ✅ yes · ❌ no · `*` launch agency/location + filter logic · `†` broadcast per-type toggle.

| Type | `notification_type` | Server sends (V5) | Android recv | Android shows | iOS recv | iOS shows | Channel | Tap target |
|---|---|---|---|---|---|---|---|---|
| **Launch** |
| 24-hour | `twentyFourHour` | ✅ | ✅ | ✅ * | ✅ | ✅ * | `LAUNCH_REMINDERS` | launch detail |
| 1-hour | `oneHour` | ✅ | ✅ | ✅ * | ✅ | ✅ * | `LAUNCH_REMINDERS` | launch detail |
| 10-minute | `tenMinutes` | ✅ | ✅ | ✅ * | ✅ | ✅ * | `LAUNCH_IMMINENT` | launch detail |
| 1-minute | `oneMinute` | ✅ | ✅ | ✅ * | ✅ | ✅ * | `LAUNCH_IMMINENT` | launch detail |
| Schedule changed | `netstampChanged` | ✅ | ✅ | ✅ * | ✅ | ✅ * | `SCHEDULE_CHANGES` | launch detail |
| Webcast live | `webcastLive` | ✅ | ✅ | ✅ * | ✅ | ✅ * | `WEBCAST_NOTIFICATIONS` | launch detail |
| In-flight | `inFlight` | ✅ | ✅ | ✅ * | ✅ | ✅ * | `LAUNCH_STATUS_UPDATES` | launch detail |
| Success | `success` | ✅ | ✅ | ✅ * | ✅ | ✅ * | `LAUNCH_STATUS_UPDATES` | launch detail |
| Failure | `failure` | ✅ | ✅ | ✅ * | ✅ | ✅ * | `LAUNCH_STATUS_UPDATES` | launch detail |
| Partial failure | `partial_failure` | ✅ | ✅ | ✅ * | ✅ | ✅ * | `LAUNCH_STATUS_UPDATES` | launch detail |
| **Event** |
| Event | `event_notification` | ✅ | ✅ | ✅ † | ✅ | ✅ † | `SPACE_EVENTS` | event detail |
| Event webcast | `event_webcast` | ✅ | ✅ | ✅ † | ✅ | ✅ † | `SPACE_EVENTS` | event detail |
| **News** |
| Featured news | `featured_news` | ✅ | ✅ | ✅ † | ✅ | ✅ † | `NEWS_UPDATES` | `article_url` (external browser) |
| **Custom** |
| Custom admin | `custom` | ✅ | ✅ | ✅ † | ✅ | ✅ † | `ANNOUNCEMENTS` | by `target_type` (see below) |

`*` Launches are filtered by agency/location/webcast-only (and follow-all/strict mode).
`†` Broadcast types (event/news/custom) are gated by the global kill switch **and** their own
per-type toggle (`EVENTS` / `FEATURED_NEWS` / `ANNOUNCEMENTS`) — **not** agency/location.

## Detection order (KMP)

Both the Android `NotificationWorker` and the iOS receipt paths classify a payload in this
order — markers, not equality except for custom:

1. `notification_type == "custom"` → **custom** (`CustomNotificationPayload`)
2. `event_id` present → **event** (`EventNotificationPayload`)
3. `article_id` present → **news** (`NewsNotificationPayload`)
4. `lsp_id` present → **V5 launch** (`V5NotificationPayload`)
5. else → legacy V4

Custom is checked **first** so a custom notification that references an event (carrying an
event target) is never mis-detected as an event. Verified on Android via payload trace
(custom check returns before the event branch).

## Filtering (why "received" ≠ "shown")

Two distinct models:

**Launch** (agency/location-scoped):
1. Kill switch (`enableNotifications`).
2. `webcastOnly` — only `webcast == true` payloads shown.
3. `followAllLaunches` bypass.
4. Agency/location match (`lsp_id` + `location_id`), strict vs. flexible mode.

**Broadcast (event / news / custom)** — broadcast to everyone; gated only by:
1. Kill switch (`enableNotifications`).
2. The type's own per-type toggle: `EVENTS`, `FEATURED_NEWS`, `ANNOUNCEMENTS`
   (default-on; surfaced as settings rows; persisted in `topic_settings`).

These run in three places — Android `NotificationWorker`, the iOS foreground delegate, and the
iOS NSE — all reading consistent values.

### iOS NSE + foreground (app killed and app open)

- **NSE (killed):** the NSE detects a V5 launch by `lsp_id`; broadcast types (no `lsp_id`) take
  the non-V5 branch and are gated by per-type toggles bridged into the App Group as
  `nse_topic_events` / `nse_topic_featured_news` / `nse_topic_announcements`
  (written by `NSEPreferenceBridge`, read by `NSEFilterPreferences` /
  `NotificationService.isBroadcastTypeAllowed`, default-true on missing, kill switch first).
- **Foreground (app open):** `AppDelegate.willPresent` recognizes custom/event/news (order
  custom → event → news) and presents `[.banner,.badge,.sound]` gated by
  `broadcastForegroundAllowed(toggleKey:)`, which reads the **same** App Group keys as the NSE —
  so foreground and killed-app behavior are consistent. Launches are not diverted into this
  branch; they keep their filtered `parseNotificationData → shouldShowNotification` path.

## Tap / deep-linking

- **Launch** → launch detail (Android `launch_uuid` + `is_v5=true` extras; iOS
  `setNotificationLaunchId`).
- **Event** → event detail (Android `event_id` extra; iOS `setNotificationEventId` — newly
  wired end-to-end).
- **News** → opens `article_url` in the **external browser** (Android `ACTION_VIEW`
  `PendingIntent`; iOS `UIApplication.open`), matching the in-app news list behavior.
- **Custom** → routes by `target_type`: `launch` → launch detail, `event` → event detail,
  `news` → open `target_url` externally, `none` → app home.

## Display sources

- **Android receipt:** `SpaceLaunchFirebaseMessagingService` → enqueues `NotificationWorker`.
- **Android routing:** `NotificationWorker.kt` — detection order above; branches to
  `processCustomNotification` / `processEventNotification` / `processNewsNotification` /
  `processV5Notification` / V4.
- **Android display:** `NotificationDisplayHelper.kt` — `showV5Notification`,
  `showEventNotification`, `showNewsNotification`, `showCustomNotification`; channel via
  `getChannelId()`.
- **Payload parsers:** `V5NotificationPayload`, `EventNotificationPayload`,
  `NewsNotificationPayload` (new), `CustomNotificationPayload` (new); shared keys in
  `NotificationTopicConfig.PayloadFields`.
- **iOS:** `iosApp/iosApp/AppDelegate.swift` (foreground/background/tap), `MainViewController.kt`
  (`setNotificationLaunchId` / `setNotificationEventId` bridges), and
  `iosApp/NotificationServiceExtension/NotificationService.swift` + `NSEFilterPreferences.swift`
  (killed).

## Remaining gaps

1. **`failure` / `partial_failure` have no user toggle** — always shown when the launch passes
   its agency/location filter (they fall through to allowed-by-default).
2. **V5 launch per-type filtering is incomplete.** `V5NotificationFilter` still has a `// TODO`
   for per-type checks, so the killed-app NSE path does not gate V5 launches by their per-type
   toggles (24h/1h/etc.); the foreground path uses the V4-style filter. The two can diverge —
   a foreground banner could show that the NSE would suppress, or vice-versa. Pre-existing,
   out of scope of the news/custom work.
3. **iOS is code-review-verified, not compiled** — a Mac/Xcode build + on-device push smoke
   test is the remaining gate before a production release. Live FCM delivery / killed-app NSE
   behavior is verified by code path, not real device push.

## What is NOT changed by this document

This is a documentation/analysis record. No code changes are prescribed here; it reflects the
implemented state of V5 launch/event/news/custom dispatch and the KMP handlers.
