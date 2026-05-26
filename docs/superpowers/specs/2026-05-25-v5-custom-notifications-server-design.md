# V5 Custom Admin Notifications for KMP — Server

**Date:** 2026-05-25
**Status:** Approved
**Repo:** SpaceLaunchNow-Server
**Companion spec:** `SpaceLaunchNow-KMP-Main/docs/superpowers/specs/2026-05-25-v5-custom-notifications-kmp-design.md`

## Problem

Custom admin push notifications (`CustomNotificationMixin.send_custom_ios_v3` /
`send_custom_android_v3`) only target V3 topics. Under the V5-only change, `check_custom` in
`bot/app/notifications/launch_event_tracker.py` was set to **early-return** (so pending records
are not silently marked complete and dropped). Custom notifications are therefore currently
**dark**. This spec restores them on the V5 path.

A custom notification optionally references a launch, a news article, or an event (or nothing).
That target must survive into the flat V5 payload so the KMP app can deep-link on tap.

## Approach

Add V5 send + payload-builder methods to `CustomNotificationMixin`, mirroring the event/news
V5 pattern, and replace the `check_custom` early-return with V5 dispatch that honors the
existing `send_ios` / `send_android` flags.

## Architecture

### Files changed

- `src/bot/app/notifications/custom.py` — add `_build_v5_custom_data(pending)` and
  `_send_v5_custom_notification(pending)`. Existing `send_custom_ios_v3` /
  `send_custom_android_v3` retained, uninvoked.
- `src/bot/app/notifications/launch_event_tracker.py` — replace the `check_custom`
  early-return with V5 dispatch (see below).

### Source model (unchanged)

`bot/models.py` `Notification`: `launch_id` (UUID, nullable), `news_id` (str, nullable),
`event_id` (int, nullable), `title`, `message`, `send_ios`, `send_ios_complete`,
`send_android`, `send_android_complete`. The three id fields are mutually exclusive in
practice (the existing `get_json_data` treats them as such).

### Payload contract (shared with KMP spec)

`_build_v5_custom_data(pending)` returns a **flat string dict**. The launch/news/event
reference collapses to a `target_type` + `target_id` (+ `target_url` for news):

```python
{
    "notification_type": "custom",        # DETECTION MARKER — checked FIRST by KMP
    "title": pending.title,
    "body": pending.message,
    "custom_id": str(pending.id),         # collapse key
    "target_type": target_type,           # "launch" | "event" | "news" | "none"
    "target_id": target_id,               # launch uuid / event id / article id, or ""
    "target_url": target_url,             # article.link for news targets, else ""
    "custom_image": image or "",          # optional display image from the target
}
```

Mapping from the `Notification` row:

| Row field set | `target_type` | `target_id` | `target_url` | `custom_image` |
|---|---|---|---|---|
| `launch_id` | `launch` | `str(launch.id)` | `""` | launch image / LSP image |
| `news_id` | `news` | `str(article.id)` | `article.link` | `article.featured_image` |
| `event_id` | `event` | `str(event.id)` | `""` | event feature image |
| none | `none` | `""` | `""` | `""` |

> **Why `notification_type=="custom"` is the marker (not `target_id`):** a custom notification
> that references an event would otherwise carry an `event_id` and be mis-detected as an event
> by the KMP app. The KMP detection order checks `notification_type=="custom"` **before**
> `event_id`/`article_id`/`lsp_id`. See the KMP spec.

### Send methods

Two platform-specific methods sharing `_build_v5_custom_data`, mirroring the existing
`send_custom_ios_v3` / `send_custom_android_v3` split (so a record flagged for both platforms
is sent once per platform, never doubled):

- **`_send_v5_custom_android(pending)`** — data-only to the Android V5 topic,
  `collapse_key=f"custom_{custom_id}"`, `analytics_label=f"v5_android_custom_{custom_id}"`,
  `priority: high`, `ttl: "86400s"`.
- **`_send_v5_custom_ios(pending)`** — alert (`title`/`body`) to the iOS V5 topic,
  `apns-priority: 10`, `aps.mutable-content: 1`,
  `analytics_label=f"v5_ios_custom_{custom_id}"`.

### Tracker change (`check_custom`)

Replace the early-return with two platform loops (matching the original V3 structure), each
calling only its platform method and marking only its own `_complete` flag:

```python
def check_custom(self):
    pending_ios = Notification.objects.filter(Q(send_ios=True) & Q(send_ios_complete=False))
    pending_android = Notification.objects.filter(Q(send_android=True) & Q(send_android_complete=False))
    for pending in pending_ios:
        self.notification_handler._send_v5_custom_ios(pending)
        pending.send_ios_complete = True
        pending.save()
    for pending in pending_android:
        self.notification_handler._send_v5_custom_android(pending)
        pending.send_android_complete = True
        pending.save()
```

Mark `_complete` **after** the send (not before), so a send failure leaves the record
re-queued rather than silently consumed. A record flagged for both platforms appears in both
querysets and is sent once to each — never twice to the same platform.

## Topics

Same V5 topics as launches/events/news. Broadcast; client-side filtered by the new
`ANNOUNCEMENTS` toggle (KMP spec).

## What is NOT changed

- `Notification` model — no schema change.
- `get_json_data` / `send_custom_*_v3` — retained, uninvoked.
- Admin UI for creating custom notifications — unchanged.

## Testing

- Create a `Notification` with `send_ios`/`send_android` set, once each with a launch ref, a
  news ref, an event ref, and none.
- Run `run_check_custom_notification`; verify the V5 payload `target_type`/`target_id`/
  `target_url` match the table above, and `_complete` flips only after send.
- Verify a launch-ref custom carries `notification_type="custom"` (not mis-typed as a launch).
