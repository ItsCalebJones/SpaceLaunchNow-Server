# iOS Notification Collapse (`apns-collapse-id`) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make iOS notifications collapse like Android by adding an `apns-collapse-id` header to every V5 iOS push, keyed per entity.

**Architecture:** Each of the four V5 iOS send sites (launch, event, news, custom) already computes a per-entity key for its Android `collapse_key`. We mirror that same string into the iOS `apns_config["headers"]` so APNs replaces the prior notification for that entity. No payload, topic, Android, or wrapper changes.

**Tech Stack:** Python 3.12, Django, `pyfcm` (`FCMNotification`), Firebase Cloud Messaging v1 (`apns_config` → APNs headers). Tests: Django `SimpleTestCase` with a mocked `self.fcm`.

**Spec:** `docs/superpowers/specs/2026-06-20-ios-apns-collapse-id-design.md`

## Global Constraints

- `apns-collapse-id` value MUST be ≤ 64 bytes (all four keys comply: UUID = 36 chars; prefixed integer ids < 20).
- Reuse the EXACT per-entity key already used for that type's Android `collapse_key`:
  - Launch → `data["launch_uuid"]`
  - Event → `f"event_{v5_data['event_id']}"`
  - News → `f"news_{v5_data['article_id']}"`
  - Custom → `f"custom_{v5_data['custom_id']}"`
- Do NOT change Android config, payload fields, topics, `apns-priority`, `mutable-content`, or TTL.
- V5-only. Do NOT touch V3/V4/Flutter senders.
- The change in every task is a single new key inside the existing `apns_config["headers"]` dict.
- Run tests from the repo root: `poetry run python src/manage.py test bot.tests.test_apns_collapse_id -v 2`.
- Commit style: Conventional Commits. Do NOT add a Claude co-author.

---

### Task 1: Launch `apns-collapse-id` + shared test helper

**Files:**
- Modify: `src/bot/app/notifications/v5.py` (method `send_notif_v5_ios`, the `apns_config["headers"]` block ~lines 62-71)
- Test: `src/bot/tests/test_apns_collapse_id.py` (create)

**Interfaces:**
- Consumes: `V5NotificationMixin.send_notif_v5_ios(self, data, topics, message_title=None, message_body=None, analytics_label=None)`. After this task it reads `data["launch_uuid"]`.
- Produces: module-level test helper `_ios_apns_headers(fcm_mock) -> dict` reused by Tasks 2-4.

- [ ] **Step 1: Write the failing test**

Create `src/bot/tests/test_apns_collapse_id.py`:

```python
"""Tests that every V5 iOS push sets apns-collapse-id to the per-entity key.

Test-only. Each test mocks self.fcm and inspects the apns_config headers of the
iOS notify() call. No DB, no live FCM. Runs under the Django test runner.
"""

from unittest import mock

from django.test import SimpleTestCase

from bot.app.notifications.v5 import V5NotificationMixin


def _ios_apns_headers(fcm_mock) -> dict:
    """Return the apns_config['headers'] dict from the iOS notify() call.

    The combined send methods call fcm.notify twice (Android then iOS); only the
    iOS call passes apns_config, so we select that one.
    """
    for call in fcm_mock.notify.call_args_list:
        apns = call.kwargs.get("apns_config")
        if apns:
            return apns["headers"]
    raise AssertionError("no iOS notify() call with apns_config was made")


class LaunchCollapseIdTests(SimpleTestCase):
    def setUp(self):
        self.mixin = V5NotificationMixin()
        self.mixin.fcm = mock.MagicMock()
        self.mixin.DEBUG = True

    def test_ios_sets_apns_collapse_id_to_launch_uuid(self):
        data = {"notification_type": "oneHour", "launch_uuid": "uuid-123"}
        self.mixin.send_notif_v5_ios(data=data, topics="'prod_v5_ios' in topics")
        headers = _ios_apns_headers(self.mixin.fcm)
        self.assertEqual(headers["apns-collapse-id"], "uuid-123")

    def test_ios_keeps_existing_priority_header(self):
        data = {"notification_type": "oneHour", "launch_uuid": "uuid-123"}
        self.mixin.send_notif_v5_ios(data=data, topics="'prod_v5_ios' in topics")
        headers = _ios_apns_headers(self.mixin.fcm)
        self.assertEqual(headers["apns-priority"], "10")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `poetry run python src/manage.py test bot.tests.test_apns_collapse_id.LaunchCollapseIdTests -v 2`
Expected: FAIL — `test_ios_sets_apns_collapse_id_to_launch_uuid` raises `KeyError: 'apns-collapse-id'` (header not present yet). `test_ios_keeps_existing_priority_header` passes.

- [ ] **Step 3: Add the header in `send_notif_v5_ios`**

In `src/bot/app/notifications/v5.py`, change the iOS `apns_config` headers from:

```python
                apns_config={
                    "headers": {
                        "apns-priority": "10",
                    },
```

to:

```python
                apns_config={
                    "headers": {
                        "apns-priority": "10",
                        "apns-collapse-id": data["launch_uuid"],
                    },
```

- [ ] **Step 4: Run test to verify it passes**

Run: `poetry run python src/manage.py test bot.tests.test_apns_collapse_id.LaunchCollapseIdTests -v 2`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add src/bot/app/notifications/v5.py src/bot/tests/test_apns_collapse_id.py
git commit -m "feat(notifications): collapse V5 iOS launch pushes via apns-collapse-id"
```

---

### Task 2: Event `apns-collapse-id`

**Files:**
- Modify: `src/bot/app/events/notification_handler.py` (method `_send_v5_event_notification`, iOS `apns_config["headers"]` ~lines 147-156)
- Test: `src/bot/tests/test_apns_collapse_id.py` (append class)

**Interfaces:**
- Consumes: `EventNotificationHandler._send_v5_event_notification(self, event, event_type, webcast=False)`, which builds `v5_data = self._build_v5_event_data(event, event_type, webcast)`. Uses `_ios_apns_headers` from Task 1.
- Produces: nothing downstream.

- [ ] **Step 1: Write the failing test**

Append to `src/bot/tests/test_apns_collapse_id.py`:

```python
from bot.app.events.notification_handler import EventNotificationHandler


class EventCollapseIdTests(SimpleTestCase):
    def setUp(self):
        # Subclass of NotificationService whose __init__ needs FCM creds — bypass it.
        self.handler = EventNotificationHandler.__new__(EventNotificationHandler)
        self.handler.fcm = mock.MagicMock()
        self.handler.DEBUG = True

    def test_ios_sets_apns_collapse_id_with_event_prefix(self):
        v5 = {"notification_type": "event", "title": "t", "body": "b", "event_id": "999"}
        with mock.patch.object(self.handler, "_build_v5_event_data", return_value=v5):
            self.handler._send_v5_event_notification(event=object(), event_type="event")
        headers = _ios_apns_headers(self.handler.fcm)
        self.assertEqual(headers["apns-collapse-id"], "event_999")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `poetry run python src/manage.py test bot.tests.test_apns_collapse_id.EventCollapseIdTests -v 2`
Expected: FAIL — `KeyError: 'apns-collapse-id'`.

- [ ] **Step 3: Add the header in `_send_v5_event_notification`**

In `src/bot/app/events/notification_handler.py`, change the iOS `apns_config` headers from:

```python
                apns_config={
                    "headers": {
                        "apns-priority": "10",
                    },
```

to:

```python
                apns_config={
                    "headers": {
                        "apns-priority": "10",
                        "apns-collapse-id": f"event_{v5_data['event_id']}",
                    },
```

- [ ] **Step 4: Run test to verify it passes**

Run: `poetry run python src/manage.py test bot.tests.test_apns_collapse_id.EventCollapseIdTests -v 2`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/bot/app/events/notification_handler.py src/bot/tests/test_apns_collapse_id.py
git commit -m "feat(notifications): collapse V5 iOS event pushes via apns-collapse-id"
```

---

### Task 3: News `apns-collapse-id`

**Files:**
- Modify: `src/bot/app/notifications/news_notification_handler.py` (method `_send_v5_notification`, iOS `apns_config["headers"]` ~lines 82-91)
- Test: `src/bot/tests/test_apns_collapse_id.py` (append class)

**Interfaces:**
- Consumes: `NewsNotificationHandler._send_v5_notification(self, article)`, which builds `v5_data = self._build_v5_news_data(article)`. Uses `_ios_apns_headers` from Task 1.

- [ ] **Step 1: Write the failing test**

Append to `src/bot/tests/test_apns_collapse_id.py`:

```python
from bot.app.notifications.news_notification_handler import NewsNotificationHandler


class NewsCollapseIdTests(SimpleTestCase):
    def setUp(self):
        self.handler = NewsNotificationHandler.__new__(NewsNotificationHandler)
        self.handler.fcm = mock.MagicMock()
        self.handler.DEBUG = True

    def test_ios_sets_apns_collapse_id_with_news_prefix(self):
        v5 = {"notification_type": "featured_news", "title": "t", "body": "b", "article_id": "777"}
        with mock.patch.object(self.handler, "_build_v5_news_data", return_value=v5):
            self.handler._send_v5_notification(article=object())
        headers = _ios_apns_headers(self.handler.fcm)
        self.assertEqual(headers["apns-collapse-id"], "news_777")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `poetry run python src/manage.py test bot.tests.test_apns_collapse_id.NewsCollapseIdTests -v 2`
Expected: FAIL — `KeyError: 'apns-collapse-id'`.

- [ ] **Step 3: Add the header in `_send_v5_notification`**

In `src/bot/app/notifications/news_notification_handler.py`, change the iOS `apns_config` headers from:

```python
                apns_config={
                    "headers": {
                        "apns-priority": "10",
                    },
```

to:

```python
                apns_config={
                    "headers": {
                        "apns-priority": "10",
                        "apns-collapse-id": f"news_{v5_data['article_id']}",
                    },
```

- [ ] **Step 4: Run test to verify it passes**

Run: `poetry run python src/manage.py test bot.tests.test_apns_collapse_id.NewsCollapseIdTests -v 2`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/bot/app/notifications/news_notification_handler.py src/bot/tests/test_apns_collapse_id.py
git commit -m "feat(notifications): collapse V5 iOS news pushes via apns-collapse-id"
```

---

### Task 4: Custom `apns-collapse-id`

**Files:**
- Modify: `src/bot/app/notifications/custom.py` (method `_send_v5_custom_ios`, iOS `apns_config["headers"]` ~lines 108-117)
- Test: `src/bot/tests/test_apns_collapse_id.py` (append class)

**Interfaces:**
- Consumes: `CustomNotificationMixin._send_v5_custom_ios(self, pending)`, which builds `v5_data = self._build_v5_custom_data(pending)`. Uses `_ios_apns_headers` from Task 1.

- [ ] **Step 1: Write the failing test**

Append to `src/bot/tests/test_apns_collapse_id.py`:

```python
from bot.app.notifications.custom import CustomNotificationMixin


class CustomCollapseIdTests(SimpleTestCase):
    def setUp(self):
        self.mixin = CustomNotificationMixin()
        self.mixin.fcm = mock.MagicMock()
        self.mixin.DEBUG = True

    def test_ios_sets_apns_collapse_id_with_custom_prefix(self):
        v5 = {"notification_type": "custom", "title": "t", "body": "b", "custom_id": "cust-1"}
        with mock.patch.object(self.mixin, "_build_v5_custom_data", return_value=v5):
            self.mixin._send_v5_custom_ios(pending=object())
        headers = _ios_apns_headers(self.mixin.fcm)
        self.assertEqual(headers["apns-collapse-id"], "custom_cust-1")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `poetry run python src/manage.py test bot.tests.test_apns_collapse_id.CustomCollapseIdTests -v 2`
Expected: FAIL — `KeyError: 'apns-collapse-id'`.

- [ ] **Step 3: Add the header in `_send_v5_custom_ios`**

In `src/bot/app/notifications/custom.py`, change the iOS `apns_config` headers from:

```python
                apns_config={
                    "headers": {
                        "apns-priority": "10",
                    },
```

to:

```python
                apns_config={
                    "headers": {
                        "apns-priority": "10",
                        "apns-collapse-id": f"custom_{v5_data['custom_id']}",
                    },
```

- [ ] **Step 4: Run the full test module to verify all four pass**

Run: `poetry run python src/manage.py test bot.tests.test_apns_collapse_id -v 2`
Expected: PASS (all classes — launch, event, news, custom).

- [ ] **Step 5: Commit**

```bash
git add src/bot/app/notifications/custom.py src/bot/tests/test_apns_collapse_id.py
git commit -m "feat(notifications): collapse V5 iOS custom pushes via apns-collapse-id"
```

---

## Device verification (after merge, with the client built)

Automated tests prove the header is emitted; collapse itself is APNs runtime behavior. On a real iOS device with the app **force-quit**:

1. Send `oneHour` then `tenMinutes` for the **same** launch → one notification, showing `tenMinutes` (not two).
2. Send notifications for **two different** launches → two separate notifications (guards against an over-broad key).
3. Resend the same custom/news/event notification twice → single entry each.

Use the debug send paths (`src/bot/app/notifications/debug.py`) or the in-app iOS test helpers as triggers.

## Self-review notes

- Spec coverage: all four send sites from the spec's contract table have a task. ✔
- The `_ios_apns_headers` helper selects the iOS call by the presence of `apns_config`, which only the iOS send passes — robust against the Android call in the combined event/news methods. ✔
- `apns-priority` assertion in Task 1 guards against accidentally replacing the headers dict instead of extending it. ✔
