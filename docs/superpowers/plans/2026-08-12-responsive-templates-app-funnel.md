# Responsive Templates + iOS App Funnel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Serve one identical HTML document per URL regardless of User-Agent, so the page is cacheable and Googlebot-smartphone sees a full-strength page, and give iOS users a path into the app.

**Architecture:** Delete the two `_mobile` templates and the `user_agent.is_mobile` branches that select them; reconcile the desktop/mobile differences by separating semantic heading *level* from visual *size* (Material Kit `.h1`–`.h6` utility classes). Replace five inline `is_mobile` video-sizing branches with a single click-to-play facade partial whose markup is viewport-independent. Add two User-Agent-independent app-funnel endpoints.

**Tech Stack:** Django 5 templates, `django-embed-video==1.4.10`, Material Kit CSS, vanilla JS (no framework), Django test client.

## Global Constraints

- Canonical domain is `spacelaunchnow.app`. Never emit `spacelaunchnow.me` in a canonical, `og:url`, or app-association file.
- **No rendering may depend on User-Agent.** Any template output that differs between an iPhone UA and a desktop UA is a defect. Responsiveness is CSS-only.
- `django_user_agents` stays installed; the middleware stays in `MIDDLEWARE`. Only *rendering* decisions are removed.
- Exactly one `<h1>` per rendered page.
- Preserve current desktop visual sizing. When a heading changes semantic level, add the Material Kit utility class matching its **previous** level (`<h1 class="title h3">` renders at h3 size). Verified present in `src/static/material_kit/css/material-kit.min.css` as `h1,.h1` … `h6,.h6`.
- App Store ID `1399715731`; iOS bundle `me.spacelaunchnow.spacelaunchnow`; Apple Team ID `4T4QRN2U5X`.
- Run tests with `poetry run python src/manage.py test src/` (see `Makefile:31`). Full Docker run is `make test`.
- Working tree currently has uncommitted Maps-embed changes (`referrerpolicy`, `urlencode`) in both launch-detail templates. **Preserve them**; they must survive into the merged template.

---

## File Structure

| File | Responsibility |
|---|---|
| `src/web/views.py` | Remove both `is_mobile` template selections; add `apple_app_site_association` view |
| `src/spacelaunchnow/urls.py` | Route `/.well-known/apple-app-site-association` |
| `src/web/templates/web/partials/video_embed.html` | **New.** Click-to-play facade; knows only about a video URL |
| `src/static/css/video-facade.css` | **New.** Thumbnail + play-button positioning inside the existing `.videoWrapper` box |
| `src/static/js/video-facade.js` | **New.** One delegated click listener that swaps in the iframe |
| `src/web/templates/web/base.html` | Smart App Banner meta; link the new CSS/JS; drop unused `{% load user_agents %}` |
| `src/web/templates/web/index.html` | Absorbs `index_mobile.html`, then that file is deleted |
| `src/web/templates/web/launches/launch_detail_page.html` | Absorbs `launch_detail_page_mobile.html`, then that file is deleted |
| `src/web/templates/web/{starship/starship_detail,events/event_detail,app}.html` | Swap inline `is_mobile` video branch for the facade |
| `src/web/tests.py` | UA-invariance, single-`h1`, facade, AASA and banner tests |

---

## Task 1: `apple-app-site-association` endpoint

Independent of all template work. Ship first so it is provably isolated.

**Files:**
- Modify: `src/web/views.py` (add view next to `asset_file` at line 65)
- Modify: `src/spacelaunchnow/urls.py` (add route next to the assetlinks route at line 161)
- Test: `src/web/tests.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `web.views.apple_app_site_association(request) -> HttpResponse` returning `application/json`.

- [ ] **Step 1: Write the failing test**

Append to `class WebTests` in `src/web/tests.py`:

```python
    def test_apple_app_site_association(self):
        """Universal Links require this served as JSON, at this exact path, with
        no redirect and no file extension."""
        response = self.client.get("/.well-known/apple-app-site-association")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/json")
        payload = json.loads(response.content.decode())
        details = payload["applinks"]["details"]
        self.assertEqual(details[0]["appIDs"], ["4T4QRN2U5X.me.spacelaunchnow.spacelaunchnow"])
        paths = [c["/"] for c in details[0]["components"]]
        self.assertIn("/launch/*", paths)
```

Add `import json` to the top of `src/web/tests.py` if not already present.

- [ ] **Step 2: Run test to verify it fails**

Run: `poetry run python src/manage.py test src.web.tests.WebTests.test_apple_app_site_association -v 2`
Expected: FAIL — 404, because no route exists yet.

- [ ] **Step 3: Add the view**

In `src/web/views.py`, directly below `asset_file` (which ends at line 80):

```python
def apple_app_site_association(request):
    """Apple Universal Links association file.

    Inert until the iOS app ships the `com.apple.developer.associated-domains`
    entitlement (`applinks:spacelaunchnow.app`); served now so that change is a
    one-line edit. Apple requires HTTPS, application/json, no redirect and no
    file extension.
    """
    json_data = {
        "applinks": {
            "details": [
                {
                    "appIDs": ["4T4QRN2U5X.me.spacelaunchnow.spacelaunchnow"],
                    "components": [
                        {"/": "/launch/*"},
                        {"/": "/event/*"},
                        {"/": "/astronaut/*"},
                    ],
                }
            ]
        }
    }
    return HttpResponse(json.dumps(json_data), content_type="application/json")
```

`json` and `HttpResponse` are already imported in this module (used by `asset_file`); confirm before adding duplicates.

- [ ] **Step 4: Add the route**

In `src/spacelaunchnow/urls.py`, immediately after the assetlinks line (161):

```python
        re_path(
            r"^\.well-known/apple-app-site-association$",
            landing_views.apple_app_site_association,
        ),
```

The `$` anchor matters — without it the pattern would also swallow extension-suffixed paths.

- [ ] **Step 5: Run test to verify it passes**

Run: `poetry run python src/manage.py test src.web.tests.WebTests.test_apple_app_site_association -v 2`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/web/views.py src/spacelaunchnow/urls.py src/web/tests.py
git commit -m "feat(web): serve apple-app-site-association for iOS universal links"
```

---

## Task 2: iOS Smart App Banner

**Files:**
- Modify: `src/web/templates/web/base.html`
- Test: `src/web/tests.py`

**Interfaces:**
- Consumes: nothing.
- Produces: an `apple-itunes-app` meta tag on every page that extends `base.html`.

- [ ] **Step 1: Write the failing test**

```python
    def test_smart_app_banner_present(self):
        """iOS Safari renders this natively; other browsers ignore it, so it is
        safe to send to everyone and must not be UA-conditional."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('name="apple-itunes-app"', response.content.decode())
        self.assertIn("app-id=1399715731", response.content.decode())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `poetry run python src/manage.py test src.web.tests.WebTests.test_smart_app_banner_present -v 2`
Expected: FAIL — `'name="apple-itunes-app"' not found`

- [ ] **Step 3: Add the meta tag**

In `src/web/templates/web/base.html`, immediately after the `<meta name="author" content="Caleb Jones">` line:

```html
    <meta name="apple-itunes-app" content="app-id=1399715731">
```

- [ ] **Step 4: Run test to verify it passes**

Run: `poetry run python src/manage.py test src.web.tests.WebTests.test_smart_app_banner_present -v 2`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/web/templates/web/base.html src/web/tests.py
git commit -m "feat(web): add iOS smart app banner"
```

---

## Task 3: Video facade partial

The one new component. Built and tested before any caller uses it.

**Files:**
- Create: `src/web/templates/web/partials/video_embed.html`
- Create: `src/static/css/video-facade.css`
- Create: `src/static/js/video-facade.js`
- Modify: `src/web/templates/web/base.html`

**Interfaces:**
- Consumes: nothing.
- Produces: an include contract —
  `{% include "web/partials/video_embed.html" with video_url=<url string> title=<string> %}`.
  `video_url` is a **URL string**, not an `embed_video` backend object. Renders nothing when falsy.

- [ ] **Step 1: Create the partial**

`src/web/templates/web/partials/video_embed.html`:

```django
{% load embed_video_tags %}
{% if video_url %}
    {% video video_url as sln_video %}
        <div class="videoWrapper sln-video-facade"
             data-video-code="{{ sln_video.code }}"
             data-video-title="{{ title|default:'Video player' }}">
            <img class="sln-video-thumb"
                 src="{{ sln_video.thumbnail }}"
                 alt="{{ title|default:'Video thumbnail' }}"
                 loading="lazy">
            <button type="button" class="sln-video-play"
                    aria-label="Play {{ title|default:'video' }}">
                <i class="material-icons">play_arrow</i>
            </button>
            <noscript>
                <a class="sln-video-fallback" href="{{ sln_video.url }}">Watch on YouTube</a>
            </noscript>
        </div>
    {% endvideo %}
{% endif %}
```

The markup contains no viewport or User-Agent conditional — that is the property the whole plan depends on.

- [ ] **Step 2: Create the CSS**

`src/static/css/video-facade.css`. `.videoWrapper` already supplies the 16:9 box
(`position: relative; padding-bottom: 56.25%; height: 0`) in
`src/static/material_kit/css/spacelaunchnow.css:17`, so only the facade children need rules:

```css
.sln-video-facade { background-color: #000; overflow: hidden; }

.sln-video-facade .sln-video-thumb {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    border: 0;
}

.sln-video-facade .sln-video-play {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 68px;
    height: 68px;
    border: 0;
    border-radius: 50%;
    background-color: rgba(0, 0, 0, 0.7);
    color: #fff;
    cursor: pointer;
    padding: 0;
}

.sln-video-facade .sln-video-play:hover,
.sln-video-facade .sln-video-play:focus {
    background-color: rgba(200, 0, 0, 0.85);
}

.sln-video-facade .sln-video-play .material-icons { font-size: 40px; line-height: 68px; }

.sln-video-facade iframe {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    border: 0;
}
```

- [ ] **Step 3: Create the JS**

`src/static/js/video-facade.js`:

```js
(function () {
    "use strict";
    document.addEventListener("click", function (event) {
        var button = event.target.closest && event.target.closest(".sln-video-play");
        if (!button) { return; }
        var wrapper = button.closest(".sln-video-facade");
        if (!wrapper) { return; }
        var code = wrapper.getAttribute("data-video-code");
        if (!code) { return; }

        var iframe = document.createElement("iframe");
        iframe.src = "https://www.youtube.com/embed/" + encodeURIComponent(code) + "?autoplay=1";
        iframe.title = wrapper.getAttribute("data-video-title") || "Video player";
        iframe.setAttribute("allow", "accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture");
        iframe.setAttribute("allowfullscreen", "");
        iframe.setAttribute("frameborder", "0");

        wrapper.innerHTML = "";
        wrapper.appendChild(iframe);
    });
}());
```

- [ ] **Step 4: Link both from `base.html`**

After the `spacelaunchnow.min.css` preload line:

```html
    <link rel="stylesheet" href="{% static 'css/video-facade.css' %}">
```

Before `</body>` (alongside the other script tags):

```html
    <script src="{% static 'js/video-facade.js' %}" defer></script>
```

- [ ] **Step 5: Write the test**

```python
    def test_video_facade_defers_the_iframe(self):
        """The facade must ship no iframe in the initial HTML -- that is what keeps
        page weight down and the markup viewport-independent."""
        response = self.client.get("/")
        html = response.content.decode()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("youtube.com/embed", html)
```

- [ ] **Step 6: Run test**

Run: `poetry run python src/manage.py test src.web.tests.WebTests.test_video_facade_defers_the_iframe -v 2`
Expected: PASS (the homepage does not yet use the facade, and today's `{% video %}` tag only renders an iframe when a webcast is live — this test locks the property in before Task 5 changes the page).

- [ ] **Step 7: Commit**

```bash
git add src/web/templates/web/partials/video_embed.html src/static/css/video-facade.css \
        src/static/js/video-facade.js src/web/templates/web/base.html src/web/tests.py
git commit -m "feat(web): add click-to-play video facade partial"
```

---

## Task 4: Switch the three standalone templates to the facade

`starship_detail.html`, `events/event_detail.html` and `app.html` each have an inline
`is_mobile` branch but no `_mobile` twin, so they convert cleanly and independently of
the merges.

**Files:**
- Modify: `src/web/templates/web/starship/starship_detail.html:70` (branch), plus its `{% load %}` lines
- Modify: `src/web/templates/web/events/event_detail.html:106`
- Modify: `src/web/templates/web/app.html:250`
- Test: `src/web/tests.py`

**Interfaces:**
- Consumes: the include contract from Task 3.
- Produces: three templates with zero `is_mobile` references.

- [ ] **Step 1: Write the failing test**

```python
    def test_no_user_agent_branching_in_templates(self):
        """Any surviving is_mobile branch reintroduces UA-dependent HTML, which is
        what makes the page uncacheable and cost the mobile <h1>."""
        import pathlib
        root = pathlib.Path(__file__).resolve().parent / "templates" / "web"
        offenders = [
            str(p.relative_to(root))
            for p in root.rglob("*.html")
            if "is_mobile" in p.read_text(encoding="utf-8", errors="replace")
        ]
        self.assertEqual(offenders, [])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `poetry run python src/manage.py test src.web.tests.WebTests.test_no_user_agent_branching_in_templates -v 2`
Expected: FAIL — lists 5 templates (`index.html`, `launches/launch_detail_page.html`, `launches/launch_detail_page_mobile.html`, `starship/starship_detail.html`, `events/event_detail.html`, `app.html`).

- [ ] **Step 3: Replace the branch in each of the three templates**

Each file keeps its existing outer `{% if %}` guard. Only the
`{% video ... as my_video %}` … `{% endvideo %}` construct (which contains the
mobile/desktop sizing branch) is replaced. Exact source expressions, read from the
current templates:

| File | Outer guard (keep) | Replace the `{% video %}` block with |
|---|---|---|
| `starship/starship_detail.html:70` | `{% if live_streams|length > 0 %}` | `{% include "web/partials/video_embed.html" with video_url=live_streams|first title="Watch Live" %}` |
| `events/event_detail.html:106` | `{% if event.video_url %}` | `{% include "web/partials/video_embed.html" with video_url=event.video_url title="Event Video" %}` |
| `app.html:250` | `{% if youtube_url %}` | `{% include "web/partials/video_embed.html" with video_url=youtube_url title="Watch" %}` |

**Intentional behaviour change on the starship page.** Its current tag is
`{% video live_streams|first query="autoplay=1&mute=1" as my_video %}` — the live stream
autoplays muted on page load. Under the facade it requires a tap/click, and then plays
with sound. That is the point of a facade (no autoplaying embed, no unconditional
YouTube payload) but it is a visible change; call it out in the PR.

Then delete `{% load user_agents %}` and `{% load embed_video_tags %}` from the top of
each file if no other tag in that file needs them.

- [ ] **Step 5: Run the test and the full suite**

Run: `poetry run python src/manage.py test src.web.tests -v 2`
Expected: `test_no_user_agent_branching_in_templates` still FAILS, now listing only
`index.html`, `launches/launch_detail_page.html`, `launches/launch_detail_page_mobile.html`.
All other tests PASS. This partial failure is expected — Tasks 5 and 6 clear the rest.

- [ ] **Step 6: Commit**

```bash
git add src/web/templates/web/starship/starship_detail.html \
        src/web/templates/web/events/event_detail.html \
        src/web/templates/web/app.html src/web/tests.py
git commit -m "refactor(web): use video facade in starship, event and app pages"
```

---

## Task 5: Merge the homepage

**Files:**
- Modify: `src/web/templates/web/index.html`
- Delete: `src/web/templates/web/index_mobile.html`
- Modify: `src/web/views.py:142-143`
- Test: `src/web/tests.py`

**Interfaces:**
- Consumes: the include contract from Task 3.
- Produces: `/` renders `web/index.html` for every User-Agent.

- [ ] **Step 1: Write the failing test**

```python
    DESKTOP_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    IPHONE_UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                 "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
                 "Mobile/15E148 Safari/604.1")

    def test_home_is_user_agent_invariant(self):
        """The cache key has no User-Agent, so any per-device difference here is
        served to the wrong device and hides the <h1> from Googlebot-smartphone."""
        desktop = self.client.get("/", HTTP_USER_AGENT=self.DESKTOP_UA)
        mobile = self.client.get("/", HTTP_USER_AGENT=self.IPHONE_UA)
        self.assertEqual(desktop.status_code, status.HTTP_200_OK)
        self.assertEqual(mobile.status_code, status.HTTP_200_OK)
        self.assertEqual(desktop.content, mobile.content)

    def test_home_has_exactly_one_h1(self):
        for ua in (self.DESKTOP_UA, self.IPHONE_UA):
            html = self.client.get("/", HTTP_USER_AGENT=ua).content.decode()
            self.assertEqual(html.count("<h1"), 1, f"wrong <h1> count for UA {ua}")
```

`/` carries no `{{ csrf_token }}`, so a raw byte comparison is valid here.

- [ ] **Step 2: Run tests to verify they fail**

Run: `poetry run python src/manage.py test src.web.tests.WebTests.test_home_is_user_agent_invariant src.web.tests.WebTests.test_home_has_exactly_one_h1 -v 2`
Expected: both FAIL — different templates are served, and `index.html` has 2 `<h1>` (the hero and "Watch Live").

- [ ] **Step 3: Remove the view branch**

`src/web/views.py`, replace lines 142-143:

```python
    user_agent = get_user_agent(request)
    template = "web/index_mobile.html" if user_agent.is_mobile else "web/index.html"
```

with nothing, and pass the template directly in the `render(...)` call below it:

```python
    return render(
        request,
        "web/index.html",
        {
```

Then delete the now-dead `first_launch_image` / `second_launch_image` context entries
from this view — they existed only for the mobile template's fixed two-card layout.
Because `index.html` is the surviving template, its `{% for %}` over `item.feature_image`
becomes the upcoming-launches layout for every device. This is the one intentional
behaviour change on this page: mobile previously showed exactly two hard-coded cards.
Remove the `get_user_agent` import if this was its last use in the module (Task 6 also
removes one; check before deleting).

- [ ] **Step 4: Reconcile the template**

In `src/web/templates/web/index.html`:

1. **Hero image.** Replace the inline `style="background-image: url('{% static 'img/header_starship.jpg' %}'); min-height: 65vh;"` on line ~105 with `class="... sln-hero"` (keep existing classes, keep `min-height` if it is not moved to CSS), and add to `{% block extrahead %}`:

```django
<style>
  .sln-hero { background-image: url('{% static "img/header_starship.jpg" %}'); min-height: 65vh; }
  @media (max-width: 767px) {
    .sln-hero { background-image: url('{% static "img/header_alt.jpg" %}'); }
  }
</style>
```

2. **Headings.** The hero `<h1 class="title mb-0">Space Launch Now</h1>` stays the single `h1`. Change the "Watch Live" `<h1 class="title ">` (line ~164) to `<h2 class="title h1">` — `h2` semantically, `h1` visually.

3. **Video.** Replace the whole `{% video youtube_urls|first as my_video %}` … `{% endvideo %}` block (lines ~168-176) with:

```django
{% include "web/partials/video_embed.html" with video_url=youtube_urls|first title="Watch Live" %}
```

4. **Discord link.** Copy the `discord.gg` anchor from `index_mobile.html` (line ~120 in that file) into the corresponding position in `index.html`. It currently exists only on mobile.

5. Delete `{% load user_agents %}` and `{% load embed_video_tags %}` from the top of `index.html` if nothing else needs them.

- [ ] **Step 5: Delete the mobile template**

```bash
git rm src/web/templates/web/index_mobile.html
```

- [ ] **Step 6: Run tests**

Run: `poetry run python src/manage.py test src.web.tests -v 2`
Expected: `test_home_is_user_agent_invariant` and `test_home_has_exactly_one_h1` PASS. `test_no_user_agent_branching_in_templates` still fails on the two launch-detail templates.

- [ ] **Step 7: Commit**

```bash
git add -A src/web/templates/web/ src/web/views.py src/web/tests.py
git commit -m "refactor(web): merge mobile homepage into one responsive template"
```

---

## Task 6: Merge the launch detail page

Highest-traffic page. **Preserve the uncommitted Maps-embed changes** (`referrerpolicy`,
`urlencode`) already present in `launch_detail_page.html`.

**Files:**
- Modify: `src/web/templates/web/launches/launch_detail_page.html`
- Delete: `src/web/templates/web/launches/launch_detail_page_mobile.html`
- Modify: `src/web/views.py:291-295`
- Test: `src/web/tests.py`

**Interfaces:**
- Consumes: the include contract from Task 3.
- Produces: `/launch/<slug>/` renders `web/launches/launch_detail_page.html` for every UA.

- [ ] **Step 1: Write the failing test**

```python
    def test_launch_detail_is_user_agent_invariant(self):
        """launch_detail_page.html emits window.CSRF_TOKEN, which is random per
        request, so it is masked before comparing. Add any future per-request value
        to the normaliser rather than weakening this assertion."""
        import re
        launch = Launch.objects.first()
        csrf_re = re.compile(r'window\.CSRF_TOKEN = "[^"]*"')

        def normalised(ua):
            html = self.client.get(
                f"/launch/{launch.slug}/", HTTP_USER_AGENT=ua
            ).content.decode()
            return csrf_re.sub('window.CSRF_TOKEN = "X"', html)

        self.assertEqual(normalised(self.DESKTOP_UA), normalised(self.IPHONE_UA))

    def test_launch_detail_has_exactly_one_h1(self):
        launch = Launch.objects.first()
        for ua in (self.DESKTOP_UA, self.IPHONE_UA):
            html = self.client.get(
                f"/launch/{launch.slug}/", HTTP_USER_AGENT=ua
            ).content.decode()
            self.assertEqual(html.count("<h1"), 1, f"wrong <h1> count for UA {ua}")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `poetry run python src/manage.py test src.web.tests.WebTests.test_launch_detail_is_user_agent_invariant src.web.tests.WebTests.test_launch_detail_has_exactly_one_h1 -v 2`
Expected: both FAIL — different templates, and the desktop template has 12 `<h1>`.

- [ ] **Step 3: Remove the view branch**

`src/web/views.py`, delete lines 291-295:

```python
    user_agent = get_user_agent(request)
    if user_agent.is_mobile:
        template = "web/launches/launch_detail_page_mobile.html"
    else:
        template = "web/launches/launch_detail_page.html"
```

and pass `"web/launches/launch_detail_page.html"` directly to `render(...)`. Remove the
`get_user_agent` import from `src/web/views.py:38` if this was its last use.

- [ ] **Step 4: Fix the heading hierarchy**

In `launch_detail_page.html`, keep line 67 `<h1 class="title text-white">{{ launch.name }}</h1>` as the sole `h1`. Demote the other eleven, adding the utility class that preserves current size:

| Line | From | To |
|---|---|---|
| 77 | `<h1 class="title text-white" style="margin: 5px;">` | `<h2 class="title text-white h1" style="margin: 5px;">` |
| 80 | same | same |
| 83 | `<h1 ... id="countdown">` | `<h2 class="title text-white h1" style="margin: 5px;" id="countdown">` |
| 116 | `<h1 class="title ">Watch the Launch</h1>` | `<h2 class="title h1">Watch the Launch</h2>` |
| 201 | `<h1 class="title">{{ launch.mission.name }}</h1>` | `<h2 class="title h1">{{ launch.mission.name }}</h2>` |
| 203 | `<h1 class="title">{{ launch.name }}</h1>` | `<h2 class="title h1">{{ launch.name }}</h2>` |
| 271 | `<h1 class="title">Updates</h1>` | `<h2 class="title h1">Updates</h2>` |
| 294 | `<h1 class="title">{{ launch.rocket.configuration.name }}</h1>` | `<h2 class="title h1">{{ launch.rocket.configuration.name }}</h2>` |
| 709 | `<h1 class="title text-white">{{ ...manufacturer.name }}</h1>` | `<h2 class="title text-white h1">…</h2>` |
| 711 | `<h1 class="title text-white">{{ launch.name }}</h1>` | `<h2 class="title text-white h1">…</h2>` |
| 773 | `<h1 id="related_news" class="title text-white">Related News</h1>` | `<h2 id="related_news" class="title text-white h1">Related News</h2>` |

Close each with `</h2>`. Line numbers are pre-edit; re-locate by content if they drift.

- [ ] **Step 5: Replace the video branch**

Replace the `{% video youtube_urls|first as my_video %}` … `{% endvideo %}` block around
line 122 with:

```django
{% include "web/partials/video_embed.html" with video_url=youtube_urls|first title="Watch the Launch" %}
```

The source is `youtube_urls|first` — the same expression the homepage uses. Note this is
**not** `vids`; `vids` is a separate context variable this template iterates as
`vids|slice:"1:"` for the "Additional Media" list further down, which is unchanged.
Then remove `{% load user_agents %}` and `{% load embed_video_tags %}` if unused.

- [ ] **Step 6: Carry over anything mobile-only**

Diff the two files for content the mobile template has that desktop lacks, and port it:

```bash
git diff --no-index --word-diff \
  src/web/templates/web/launches/launch_detail_page.html \
  src/web/templates/web/launches/launch_detail_page_mobile.html | less
```

Known-identical: the Maps embed (both already carry `referrerpolicy` + `urlencode`), so
the desktop copy is correct as-is.

- [ ] **Step 7: Delete the mobile template**

```bash
git rm src/web/templates/web/launches/launch_detail_page_mobile.html
```

- [ ] **Step 8: Run the full suite**

Run: `poetry run python src/manage.py test src/ -v 2`
Expected: ALL PASS, including `test_no_user_agent_branching_in_templates` (now zero
offenders) and the pre-existing `test_mobile_launch_detail_renders_a_date`, which still
asserts `id="date"` and `class="sln-time"` under an iPhone UA.

- [ ] **Step 9: Commit**

```bash
git add -A src/web/templates/web/launches/ src/web/views.py src/web/tests.py
git commit -m "refactor(web): merge mobile launch detail into one responsive template"
```

---

## Task 7: Cleanup and final verification

**Files:**
- Modify: `src/web/templates/web/base.html` (drop unused `{% load user_agents %}` at line 2, and the duplicate `{% load static %}`)
- Modify: `src/web/views.py` (remove `get_user_agent` import if now unused)

- [ ] **Step 1: Confirm no `is_mobile` or `user_agents` references remain in templates**

```bash
grep -rn "is_mobile\|load user_agents" src/web/templates/ || echo "clean"
```
Expected: `clean`

- [ ] **Step 2: Confirm the view no longer imports `get_user_agent` if unused**

```bash
grep -n "get_user_agent" src/web/views.py || echo "import removed"
```
If any usage remains, leave the import. `django_user_agents` stays in `INSTALLED_APPS`
and `MIDDLEWARE` either way — that is a Global Constraint.

- [ ] **Step 3: Run the whole suite**

Run: `poetry run python src/manage.py test src/ -v 2`
Expected: all PASS.

- [ ] **Step 4: Commit**

```bash
git add src/web/templates/web/base.html src/web/views.py
git commit -m "chore(web): drop unused user_agents template loads"
```

- [ ] **Step 5: Push and open the PR**

```bash
git push -u origin feat/responsive-templates-app-funnel
```

The PR body must state that **iOS Universal Links do not work yet** — the app lacks the
`com.apple.developer.associated-domains` entitlement, so the AASA endpoint is
pre-positioning only. Without this note someone will test it and file a bug.

- [ ] **Step 6: Post-deploy (record in the PR, do not automate)**

1. Verify on `staging.spacelaunchnow.app` at mobile and desktop widths — with a single
   large PR this is the only visual checkpoint.
2. After production deploy, purge caches: nginx holds device-specific copies
   (`proxy_cache_valid 200 2m`, so a 2-minute wait suffices; restarting the ingress pods
   is immediate). Cloudflare purge needs `Zone:Cache Purge` on the token, which is
   **unverified** — use the dashboard if the API rejects it.
3. Confirm live: `curl -A "<Googlebot-smartphone UA>" https://spacelaunchnow.app/ | grep -c '<h1'`
   must return `1`.

---

## Notes for the implementer

- **Why byte-equality is the load-bearing assertion.** The nginx ingress caches with
  `proxy_cache_key "$scheme$host$request_uri"` — no User-Agent — and the origin sends no
  `Vary: User-Agent`. Any per-device difference is therefore served to the wrong device.
  This was verified in production: `/launch/upcoming/` returned byte-identical responses
  (66895 bytes, `h1=1`) to both a desktop and an iPhone UA while `X-Cache-Status: HIT`.
- **Why the `<h1>` mattered.** Google indexes mobile-first. Pre-fix,
  Googlebot-smartphone received `h1_count=0` while Googlebot-desktop and bingbot received
  `h1_count=1`.
- Material Kit's `.h1`–`.h6` classes outrank element selectors (class specificity beats
  type), so `<h2 class="h1">` renders at h1 size. This is how semantic level and visual
  size are decoupled throughout.
