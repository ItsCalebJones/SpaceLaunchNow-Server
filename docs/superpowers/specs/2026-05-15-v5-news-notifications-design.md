# V5 News Notifications for KMP — Server

**Date:** 2026-05-15 (revised 2026-05-25)
**Status:** Approved
**Repo:** SpaceLaunchNow-Server
**Companion spec:** `SpaceLaunchNow-KMP-Main/docs/superpowers/specs/2026-05-25-v5-news-notifications-kmp-design.md`

## Problem

`NewsNotificationHandler` only ever sent featured-news to V3 FCM topics. The KMP app
subscribes exclusively to V5 topics (`prod_v5_android`, `prod_v5_ios`) and never received
featured news.

**Revision (2026-05-25):** the server is now **V5-only** — all V3/V4 dispatch was disabled
across every handler. The news V3 push was disabled by removing the
`news_notification_handler.send_notification(item)` call in
`bot/app/events/event_tracker.py:check_news_item` (social posting was kept). As a result news
notifications are currently **dark** until this V5 path ships. This spec is the only path that
will restore them.

## Approach

Add V5 send methods directly to `NewsNotificationHandler`, mirroring
`EventNotificationHandler._send_v5_event_notification`. No new files, no base-class changes.
`send_notification` becomes V5-only (the V3 method is left in the class, uninvoked, per the
V5-only convention).

## Architecture

### Files changed

- `src/bot/app/notifications/news_notification_handler.py` — add V5 methods, make
  `send_notification` call V5 only.
- `src/bot/app/events/event_tracker.py` — **re-enable** the `send_notification(item)` call in
  `check_news_item` (it now routes to V5).

### Payload contract (shared with KMP spec)

`_build_v5_news_data(article)` returns a **flat string dict** (no nested JSON, no
`json.dumps()` — FCM V5 requirement). All values are strings.

```python
{
    "notification_type": "featured_news",
    "title": f"New article via {article.news_site}",
    "body": article.title,
    "article_id": str(article.id),         # DETECTION MARKER — KMP routes news on this field
    "article_title": article.title,
    "article_news_site": article.news_site,
    "article_url": article.link,           # tap target (opened externally, like the news list)
    "article_image": article.featured_image or "",
}
```

`article_id` is the marker the KMP app uses to detect a news notification (it carries no
`lsp_id` and no `event_id`). See the KMP spec's detection-order section.

### Send methods

`_send_v5_notification(article)` sends to both V5 topics via `get_fcm_v5_android_topic()` /
`get_fcm_v5_ios_topic()` from `bot.utils.util`:

- **V5 Android** — data-only (`notification_title=None`, `notification_body=None`),
  `android_config={priority: high, collapse_key: f"news_{article_id}", ttl: "86400s"}`,
  `analytics_label=f"v5_android_news_{article_id}"`.
- **V5 iOS** — alert (`notification_title=data["title"]`, `notification_body=data["body"]`),
  `apns_config` headers `apns-priority: 10`, payload `aps.mutable-content: 1`,
  `analytics_label=f"v5_ios_news_{article_id}"`.

Each call wrapped in try/except with logging, matching the event handler.

### Updated method

```python
def send_notification(self, article):
    # V5-only. V3 (send_v3_notification) is retained but no longer invoked.
    self._send_v5_notification(article)
```

## Topics

| Platform | Topic (prod) | Topic (debug) |
|---|---|---|
| V5 Android | `prod_v5_android` | `debug_v5_android` |
| V5 iOS | `prod_v5_ios` | `debug_v5_ios` |

Broadcast to all V5 subscribers. Per-user filtering happens **client-side** via the
`FEATURED_NEWS` toggle (see KMP spec) — the server does not filter news by user.

## What is NOT changed

- `bot/utils/util.py` — `get_fcm_v5_android_topic` / `get_fcm_v5_ios_topic` already exist.
- `NotificationService` base class — no changes.
- `send_v3_notification` / `send_to_fcm` — retained in the class, uninvoked.
- `send_to_social` — unchanged; already fires in `check_news_item`.

## Testing

- Trigger `run_send_news_notification` against a debug device subscribed to `debug_v5_android`
  and `debug_v5_ios`.
- Verify log lines "V5 Android News Notification" / "V5 iOS News Notification".
- Verify `article_id` and `article_url` appear in the FCM data payload.
- Verify `check_news_item` now invokes `send_notification` (regression of the V5-only disable).
