# Consistent, Labeled Launch Times on the Web

**Date:** 2026-08-11
**Status:** Draft
**Repo:** SpaceLaunchNow-Server
**Origin:** Customer report — launch times on `/launch/upcoming/` carry no timezone label and
appear to alternate between UTC and viewer-local. The reporter missed launches as a result.

## Problem

Launch times are rendered **server-side in whatever timezone happens to be active**, and are never
labeled with that timezone.

Two settings establish UTC as the baseline:

- `TIME_ZONE = "UTC"` — `src/spacelaunchnow/settings/__init__.py:367`
- `USE_TZ = True` — `src/spacelaunchnow/settings/__init__.py:372`

But `django-tz-detect` overrides it per session:

- `tz_detect.middleware.TimezoneMiddleware` — `settings/__init__.py:265`
- `{% tz_detect %}` — `web/templates/web/base.html:125-126`
- `path("tz_detect/", ...)` — `spacelaunchnow/urls.py:93`

The library works by having JavaScript POST the browser's detected offset to `/tz_detect/set/`,
storing it in `request.session`, and activating it on **subsequent** requests. Its own README
states the consequence plainly:

> "Django's timezone awareness will not be available on the first page view."

So the observed behavior is:

| Condition | Rendered timezone |
|---|---|
| First page view (no session yet) | UTC |
| Every later view in that session | Viewer-local |
| Session expired / private window | UTC |
| JS blocked (adblocker, privacy mode) | UTC, permanently |

Nothing on the page indicates which of the two you are looking at. The customer's description —
"sometimes Eastern, sometimes UTC, changes back and forth, never labeled" — is an exact
description of this mechanism, not a misreading.

The unlabeled render sites:

| Location | Code |
|---|---|
| Upcoming launch cards | `web/templates/web/views/small_launch_card.html:27,29,31` |
| Launch window (detail) | `web/templates/web/launches/launch_detail_page.html:91` |
| Launch window (mobile) | `web/templates/web/launches/launch_detail_page_mobile.html:83` |
| Astronaut detail | `web/templates/web/astronaut/astronaut_detail.html:145,215` |
| Index / index mobile | `web/templates/web/index.html:147`, `index_mobile.html:145` |
| Launch database table | `web/tables/launch_table.py:18` (`net` column) |

### Secondary problem: triplicated formatter

The detail pages already solve part of this client-side, via a `getDateFormat` function that uses
`Intl.DateTimeFormat().resolvedOptions().timeZone` and emits a timezone abbreviation. It is
**duplicated verbatim in three templates** (~45 lines each):

- `launches/launch_detail_page.html:896-942`
- `launches/launch_detail_page_mobile.html:851-897`
- `events/event_detail.html:226-272`

A *second*, unrelated date library (`material_kit/js/dateFormat.js`) formats the launch window on
those same pages. The upcoming cards use neither. There is no single owner of "how a launch time
is displayed."

### Third problem: the mobile detail page shows no date at all

On `launch_detail_page_mobile.html`, `#date` is an empty element in all three status branches
(lines 70, 73, 76). The only code that would populate it is **commented out**:

```
launch_detail_page_mobile.html:900
{% comment %} document.getElementById("date").innerHTML = getDateFormat(countDownDate, {{ launch.net }}) {% endcomment %}
```

That call is also wrong on its own terms — it passes `{{ launch.net }}` (a datetime) where
`getDateFormat` expects a `netPrecisionID` integer, which is the likely reason it was disabled.
The result today: mobile launch detail pages render a countdown and a launch window, but **no
launch date**, and the 47 lines of `getDateFormat` above it are dead code.

This is a pre-existing bug independent of the timezone report. The shared tag fixes it as a side
effect, because the server-rendered fallback text is present before any JavaScript runs.

## Approach

Render every launch time client-side from a UTC ISO-8601 value, through **one** shared formatter,
showing local time and UTC together. Remove `django-tz-detect` entirely.

### Markup contract

The server emits semantic markup whose text content is an **always-labeled UTC fallback**:

```html
<time class="sln-time" datetime="2026-08-14T23:32:00+00:00" data-precision="1">
  August 14, 2026 - 23:32 UTC
</time>
```

JavaScript replaces the contents with a local-primary / UTC-secondary pair:

```
August 14, 2026 - 7:32 PM EDT
August 14, 2026 - 23:32 UTC        <- muted, smaller
```

The fallback text is load-bearing. Today the detail pages leave `#date` **empty** for JS to fill
(`launch_detail_page.html:83`), so crawlers and no-JS visitors see nothing at all. Emitting a
correct labeled UTC string is strictly better than the status quo for both SEO and accessibility,
and it means the page is never wrong — only less personalized — when JS does not run.

### Components

| Unit | Responsibility |
|---|---|
| `web/templatetags/sln_utils.py` | `{% launch_time <datetime> <precision> %}` tag — **owns the precision → display-shape mapping** |
| `web/templates/web/includes/launch_time.html` | the `<time>` element and rendered UTC fallback text |
| `static/js/launch-time.js` | UTC → local conversion only; no branching |
| `web/tables/launch_table.py` | custom `net` column emitting the same markup |

Consuming templates call the tag and know nothing about formatting. The precision mapping exists
in exactly one place, so a format change is a one-file change.

### Why the mapping lives in Python

This repo is Python-only: no `package.json`, no `node_modules`, no jest/vitest/karma config, no
`*.test.js`, and no Node step in any of the six workflows under `.github/workflows/` (`ci.yml` is
Ruff → Docker build → pytest). Browser JavaScript here is hand-written files under `src/static/`
plus vendored libraries, with no runner.

Putting a 17-way branch in JavaScript would therefore place the single most decision-dense part of
this change — the thing that decides whether a launch reads `7:32 PM EDT` or `Q3 2026` — behind
zero automated coverage, in the very file introduced to prevent that class of bug.

So the branch goes in Python, where `web/tests.py` already runs in CI, and the JavaScript is
reduced to a single unconditional code path.

### Precision handling

`net_precision` has 17 values. They split into two display classes:

| Precision IDs | Meaning | `data-shape` | Display |
|---|---|---|---|
| 0, 1, 2 | Real time-of-day (second / minute / hour) | `datetime` | Local line **+ tz abbreviation**, UTC line beneath |
| 3–16 | Coarse (morning, date, week, quarter, half, year, decade) | `date` | **Single date line, no timezone, no UTC line** |

The tag resolves the precision to a `data-shape` and renders the fallback text; JavaScript acts
only on `data-shape="datetime"` and leaves `date` elements untouched.

Attaching "UTC" to "Q3 2026" or "During the 2030s" would assert a precision the data does not
have. The current card template approximates this distinction with a `status.id == 8` /
`status.id == 2` check (`small_launch_card.html:26-32`); switching to `net_precision` makes it
correct and consistent with the detail pages.

Output strings for the time-bearing cases preserve today's detail-page formatting so the change
reads as a fix rather than a redesign.

### Date library: native `Intl`

The shared formatter is written against `Intl.DateTimeFormat`, not moment.

- `moment-timezone.min.js` (`base.html:47`) exists **only** to serve the `.tz()` calls in the
  three `getDateFormat` copies. Once those are gone, the script tag is removed (~180KB).
- `moment.min.js` (`base.html:40`) **stays** — the adjacent comment at `base.html:41-42` shows it
  is a dependency of `bootstrap-datetimepicker`.

### Removals

| Item | Location |
|---|---|
| `getDateFormat` × 3 | the three templates listed above |
| Dead commented-out call | `launch_detail_page_mobile.html:900` |
| `{% tz_detect %}` | `base.html:125-126` |
| `"tz_detect"` | `settings/__init__.py:223` (`INSTALLED_APPS`) |
| `TimezoneMiddleware` | `settings/__init__.py:265` |
| `tz_detect/` route | `spacelaunchnow/urls.py:93` |
| `django-tz-detect = "==0.4.0"` | `pyproject.toml:29` |
| `moment-timezone.min.js` tag | `base.html:47` |
| `dateFormat.js` on window line | `launch_detail_page.html:946` and mobile equivalent |

## Consequences

**Pages become cacheable again.** Per-session timezone activation made every response
user-specific, which is fundamentally incompatible with page/CDN caching. Removing it is an
infrastructure win independent of the display fix.

**The DEBUG middleware insert must be re-anchored.** `settings/__init__.py:272-273` locates the
debug toolbar by string-indexing the middleware list:

```python
MIDDLEWARE.index("tz_detect.middleware.TimezoneMiddleware") + 1
```

Removing tz_detect makes this raise `ValueError` at startup under `DEBUG`. It must be re-anchored
to another middleware in the same change.

**Mobile apps are unaffected.** They format times themselves from the API, which is UTC-native.
Nothing outside the Django templates reads the session timezone.

## Testing

`web/tests.py` is 28 lines of status-code smoke tests inheriting `LLAPITests`.

Added coverage:

- Template-tag unit tests — correct ISO-8601 `datetime` attribute and correctly labeled fallback
  text, one per display class (time-bearing vs coarse).
- Precision-class test — a coarse precision renders **no** timezone label and **no** UTC line.
- Regression test — the upcoming-launches response HTML contains a `UTC`-labeled time for a
  time-bearing launch. This pins the reported customer bug server-side.
- Regression test — the **mobile** launch detail response contains a rendered launch date, pinning
  the empty-`#date` bug described above.

- Precision-mapping test — all 17 `net_precision` values resolve to the expected `data-shape` and
  fallback string. This is the dense part of the change and it is fully covered in pytest,
  because the mapping is Python.

**Remaining gap:** the one thing still untested is the JavaScript UTC → local conversion itself.
That is now a single unconditional path — parse `datetime`, format with `Intl`, prepend a line —
so it is verified manually in a browser rather than by adding a Node toolchain to a Python repo.
No JS harness is introduced; see "Why the mapping lives in Python" above.

## Out of scope

- Redesigning the launch card layout beyond the two time lines.
- A user-selectable timezone preference (the browser's own timezone is the default, and UTC is
  always shown alongside, so there is no ambiguity left to resolve).
- Migrating other `dateFormat.js` / moment usages not on the launch-time path.
- Introducing a JavaScript test harness. This repo is deliberately Python-only, and the design
  removes the need for one by keeping branching logic server-side.
- Replying to the reporting customer — a product decision, tracked separately.
