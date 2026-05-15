# V5 News Notifications for KMP

**Date:** 2026-05-15
**Status:** Approved

## Problem

`NewsNotificationHandler` only sends to V3 FCM topics (`prod_v3`, `flutter_production_v3`). The KMP app subscribes to V5 topics (`prod_v5_android`, `prod_v5_ios`) and never receives featured news notifications.

Event and netstamp notifications already have V5 support. News is the only gap.

## Approach

Add V5 send methods directly to `NewsNotificationHandler`, mirroring the pattern established in `EventNotificationHandler`. No new files, no new base class changes.

## Architecture

### File changed

`src/bot/app/notifications/news_notification_handler.py`

### New methods

**`_build_v5_news_data(article)`**
Returns a flat string dict (no nested JSON, no `json.dumps()`). All values must be strings — FCM V5 requirement.

```python
{
    "notification_type": "featured_news",
    "title": f"New article via {article.news_site}",
    "body": article.title,
    "article_id": str(article.id),        # deep-link key for KMP
    "article_title": article.title,
    "article_news_site": article.news_site,
    "article_url": article.link,
    "article_image": article.featured_image or "",
}
```

`article_id` is the field the KMP app uses to detect this is a news notification and route to the article detail screen.

**`_send_v5_notification(article)`**
Sends to both V5 topics using `get_fcm_v5_android_topic()` and `get_fcm_v5_ios_topic()` from `bot.utils.util`.

- **V5 Android**: data-only (`notification_title=None`, `notification_body=None`), `priority=high`, `collapse_key=news_{article_id}`, `ttl=86400s`
- **V5 iOS**: alert payload (`notification_title=data["title"]`, `notification_body=data["body"]`), `apns-priority=10`, `mutable-content=1`
- `analytics_label`: `v5_android_news_{article_id}` / `v5_ios_news_{article_id}`

### Updated method

**`send_notification(article)`**
After the existing `send_v3_notification()` call, adds:
```python
self._send_v5_notification(article)
```

## Topics

| Platform | Topic (prod) | Topic (debug) |
|---|---|---|
| V5 Android | `prod_v5_android` | `debug_v5_android` |
| V5 iOS | `prod_v5_ios` | `debug_v5_ios` |

All KMP subscribers receive featured news. Client-side filtering applies if the app chooses to filter. This matches the existing events behavior.

## What is NOT changed

- `bot/utils/util.py` — `get_fcm_v5_android_topic` / `get_fcm_v5_ios_topic` already exist
- `NotificationService` base class — no changes
- All other notification handlers — untouched
- V3 behavior — unchanged; existing `send_v3_notification()` still fires

## Testing

- Manual: trigger `run_send_news_notification` management command against a debug device subscribed to `debug_v5_android` and `debug_v5_ios`
- Verify log lines for "V5 Android News Notification" and "V5 iOS News Notification"
- Verify `article_id` appears correctly in the FCM result payload
