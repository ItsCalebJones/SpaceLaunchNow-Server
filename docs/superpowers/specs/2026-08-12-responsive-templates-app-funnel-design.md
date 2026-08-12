# Responsive templates + iOS app funnel — design

**Date:** 2026-08-12
**Status:** approved, ready for implementation planning

## Problem

`web/views.py` picks a different template per device:

```python
template = "web/index_mobile.html" if user_agent.is_mobile else "web/index.html"   # :143
template = "web/launches/launch_detail_page_mobile.html" if ... else "..."          # :292
```

The response body therefore varies by User-Agent, but nothing downstream keys on
User-Agent. The nginx ingress caches with
`proxy_cache_key "$scheme$host$request_uri"` (see GitOps
`manifests/infrastructure/ingress/nginx-cache-config.yaml`) and the origin sends no
`Vary: User-Agent`. Two consequences, both verified against production on 2026-08-12:

**1. Mobile users are already served desktop HTML.** On a cached URL, both UAs get a
byte-identical response:

```
/launch/upcoming/   X-Cache-Status: HIT (4/4 requests)
  DESKTOP  h1=1  bytes=66895
  MOBILE   h1=1  bytes=66895
```

**2. The page Google indexes has no `<h1>`.** Google indexes mobile-first, and on an
uncached URL the mobile template is what Googlebot-smartphone receives:

```
Googlebot-smartphone  h1_count=0
Googlebot-desktop     h1_count=1
bingbot               h1_count=1
```

`index_mobile.html` starts at `<h2>`; the desktop template has an `<h1>`. Which one a
crawler gets depends on cache state, so the defect is intermittent — which is why it
survived this long.

Because the HTML is UA-dependent, it also cannot safely be cached at the Cloudflare
edge. `spacelaunchnow.app` currently has no HTML cache rule at all, and the rule that
used to exist on `spacelaunchnow.me` (`edge_cache_ttl=7200`) was removed precisely
because it cross-served device templates.

### What is *not* the problem

An earlier reading of this blamed `Set-Cookie: csrftoken` and `Vary: Cookie` for the
cacheability failure. That is no longer accurate. `tz_detect` has been removed from
`master` (0 occurrences in `origin/master:src/spacelaunchnow/urls.py`), and the current
origin sends **no `Set-Cookie` on any page**, including launch detail which renders
`{% csrf_token %}`. `Vary` is now only `origin` (from `corsheaders`), and several pages
already emit `Cache-Control: max-age=600`. **UA-switching is the sole remaining
blocker.**

## Goals

- One HTML document per URL, identical for every User-Agent.
- Exactly one `<h1>` per page, present for every crawler.
- No behavioural dependence on `user_agent.is_mobile` in rendering.
- Give iOS users a path into the app (currently there is none).

## Non-goals

- Removing the `django_user_agents` dependency. The middleware is harmless; only
  *rendering* decisions are removed.
- Extracting shared partials beyond the video facade.
- Adding the Cloudflare cache rule for `.app` HTML. That is the payoff, but it belongs
  in a separate change once production confirms the HTML is device-invariant.
- Shipping working iOS Universal Links (see *Dependencies*).

## Design

### Deleted

- `src/web/templates/web/index_mobile.html`
- `src/web/templates/web/launches/launch_detail_page_mobile.html`
- The UA branches at `views.py:143` and `views.py:292-295`; each collapses to a fixed
  template name.
- All five inline `{% if request|is_mobile %}` branches — in `index.html`,
  `launches/launch_detail_page.html`, `starship/starship_detail.html`,
  `events/event_detail.html`, `app.html`. Every one only sets embedded-video iframe
  dimensions (`85% x 25%` vs `100% x 450`), which is a CSS concern.
- The now-unused `{% load user_agents %}` and `{% load embed_video_tags %}` in each
  template that no longer references them.

### Heading strategy

The desktop/mobile diff is dominated by heading-*level* changes carrying identical
content and classes — `<h1 class="title">{{ launch.name }}</h1>` versus
`<h3 class="title">{{ launch.name }}</h3>`. Semantic level and visual size are
separated: the merged template picks the correct semantic level once (one `h1`, then
`h2`/`h3` in document order) and preserves apparent size with Material Kit's `.h1`–`.h6`
utility classes, which are confirmed present in
`src/static/material_kit/css/material-kit.min.css` (`h1,.h1`, `h2,.h2`, …). A class
selector outranks an element selector, so `<h1 class="title mb-0 h2">` renders at h2
size. This is the same technique already applied to the mobile homepage `h1` in PR #325.

On `launch_detail_page.html` this also resolves the existing 12-`<h1>` problem, because
the merge forces choosing a single top-level heading — `{{ launch.name }}`.

### Homepage deltas

| Delta | Today | Merged |
|---|---|---|
| Heading levels | mobile demotes `h1`→`h2`, `h2`→`h3` | one semantic `h1`, size via utility classes |
| Hero image | `header_starship.jpg` vs `header_alt.jpg`, both `min-height: 65vh` | one element, image swapped by a media query (see below) |
| Live video | absent on mobile | facade at all sizes |
| Discord link | mobile only | kept, shown at all sizes |
| Upcoming-launch cards | desktop loops `item.feature_image`; mobile uses fixed `first_launch_image` / `second_launch_image` | adopt the desktop loop |

The last row is the only intentional **behaviour change**: mobile currently shows two
hard-coded launch cards and will now get the looped list. The view already supplies both
context shapes, so `first_launch_image` / `second_launch_image` become dead and are
removed from the view along with the branch.

The hero image is currently an inline
`style="background-image: url('{% static ... %}')"`, and `{% static %}` cannot be
resolved from a static `.css` file. The merged template therefore emits a small scoped
`<style>` block in `{% block extrahead %}` carrying both resolved URLs, and the element
keeps only its class:

```django
<style>
  .sln-hero { background-image: url('{% static "img/header_starship.jpg" %}'); }
  @media (max-width: 767px) {
    .sln-hero { background-image: url('{% static "img/header_alt.jpg" %}'); }
  }
</style>
```

This stays identical for every User-Agent, so it does not reintroduce the cache problem.

`name="title"`, `name="twitter:title"` and `name="description"` are present in **both**
templates — no meta-tag reconciliation is needed.

### Launch detail deltas

Almost entirely heading demotion. `{{ launch.name }}`, `{{ status }}`, the countdown,
`#date`, "Watch the Launch", `{{ launch.mission.name }}` and
`{{ launch.rocket.configuration.name }}` all appear in both templates with identical
classes and content, differing only in level (`h1`/`h2` vs `h3`/`h4`). Resolved by the
heading strategy above.

### Video facade

One partial, `web/partials/video_embed.html`, parameterised by `video_url` and an
optional `title`:

```django
{% include "web/partials/video_embed.html" with video_url=my_video title="Watch the Launch" %}
```

It renders an aspect-ratio box (a `padding-top` percentage rather than the `aspect-ratio`
property, since Material Kit predates reliable support), a `loading="lazy"` thumbnail,
and a real `<button>` with an accessible label. One delegated listener in a small static
JS file swaps in the `<iframe>` on activation.

The load-bearing property: **the markup is identical for every viewport and every
User-Agent**; responsiveness is entirely CSS. This is what makes the page cacheable.

Contract:

- *Input:* a video URL (and optional heading text). It knows nothing about launches or events.
- *Output:* markup that upgrades to an iframe on user activation.
- *Empty input:* renders nothing, matching today's `{% if %}` guards.
- *JS unavailable:* degrades to a plain link to the video rather than a dead button.

It replaces all five inline branches, so no caller needs `{% load embed_video_tags %}`.

### iOS app funnel

Two additions, both User-Agent independent and therefore cache-safe.

**Smart App Banner** — one line in `base.html`, covering every page:

```html
<meta name="apple-itunes-app" content="app-id=1399715731">
```

iOS Safari renders it natively; every other browser ignores it.

**`apple-app-site-association`** — a JSON view mirroring the existing `asset_file` view
(`web/views.py:65`), wired next to the assetlinks route:

```python
re_path(r"^\.well-known/apple-app-site-association$", landing_views.apple_app_site_association),
```

```json
{"applinks": {"details": [{"appIDs": ["4T4QRN2U5X.me.spacelaunchnow.spacelaunchnow"],
 "components": [{"/": "/launch/*"}, {"/": "/event/*"}, {"/": "/astronaut/*"}]}]}}
```

Apple requires HTTPS, `Content-Type: application/json`, **no redirect**, and no file
extension. Components are scoped to routes with app equivalents rather than a blanket
`*`.

Reference values, from `SpaceLaunchNow-KMP-Main/iosApp/iosApp.xcodeproj/project.pbxproj`
and the existing store links:

| | |
|---|---|
| App Store ID | `1399715731` |
| Bundle ID | `me.spacelaunchnow.spacelaunchnow` |
| Team ID | `4T4QRN2U5X` |
| Existing URL scheme | `spacelaunchnow://` |

## Dependencies

**iOS Universal Links will not work when this ships, by design.** No `.entitlements`
file in `SpaceLaunchNow-KMP-Main` contains `com.apple.developer.associated-domains`.
Working Universal Links additionally require adding `applinks:spacelaunchnow.app` to
`iosApp/iosApp/iosApp.entitlements`, enabling Associated Domains on the App ID, and an
App Store release. The AASA endpoint is shipped now so that later change is a one-line
entitlement edit. **State this in the PR** so the endpoint isn't tested and reported as
broken. The Smart App Banner *does* work immediately.

**PR #325** (`fix/seo-canonical-domain`) modifies `index_mobile.html`, which this design
deletes. Expect a delete/modify conflict if #325 is still open when implementation lands;
merge #325 first.

## Testing

Extends `src/web/tests.py`, which already drives User-Agent via `HTTP_USER_AGENT`.

- **UA-invariance** — the load-bearing test. Fetch each page with an iPhone UA and a
  desktop Chrome UA; assert `assertTemplateUsed` matches and the bodies are equal.

  Comparison must account for per-request values. `launch_detail_page.html` emits
  `window.CSRF_TOKEN = "{{ csrf_token }}"`, which is random per request, so a raw
  byte-comparison there fails for reasons unrelated to User-Agent. The helper normalises
  the response before comparing:

  ```python
  CSRF_RE = re.compile(r'window\.CSRF_TOKEN = "[^"]*"')

  def _normalised(self, path, ua):
      html = self.client.get(path, HTTP_USER_AGENT=ua).content.decode()
      return CSRF_RE.sub('window.CSRF_TOKEN = "X"', html)
  ```

  `/` carries no `{{ csrf_token }}` and can be compared byte-for-byte directly. Any
  future per-request value must be added to the normaliser, not worked around by
  weakening the assertion.
- **Exactly one `<h1>`** per page, under both UAs.
- **No `<iframe>` in the initial HTML**, and the facade element present when a video exists.
- **AASA** — 200, `Content-Type: application/json`, parses as JSON, contains the correct `appID`.
- **Smart App Banner** — `apple-itunes-app` present in rendered output.
- `test_mobile_launch_detail_renders_a_date` must keep passing unchanged. It asserts on
  content (`id="date"`, `class="sln-time"`) rather than template name, so it becomes a
  genuine regression guard for the merge.

## Rollout

1. Deploy to `staging.spacelaunchnow.app`; check both pages at mobile and desktop widths.
   With a single large PR this is the only verification checkpoint.
2. Promote to production.
3. **Purge caches.** nginx holds device-specific copies (`proxy_cache_valid 200 2m`) and
   Cloudflare holds cached HTML; both will serve stale device-specific HTML after the
   merge lands. The nginx TTL is only 2 minutes, so letting it roll is sufficient there;
   restarting the ingress pods is the immediate option. For Cloudflare, purging needs
   `Zone:Cache Purge` on the API token — **not yet verified** on the cert-manager token,
   which is known to lack zone-settings and ruleset scope. Confirm before relying on an
   API purge, or purge from the dashboard.

**Risk:** visual regression on the two highest-traffic pages, with no incremental
checkpoint — the accepted cost of a single-PR approach. Rollback is reverting the PR;
there is no data migration. Note that deploying *fixes* a live defect: nginx is already
cross-serving desktop HTML to mobile users.

**Follow-up (separate change):** once production confirms device-invariant HTML, add the
Cloudflare cache rule for `.app` HTML. That is the performance payoff and needs its own
verification.
