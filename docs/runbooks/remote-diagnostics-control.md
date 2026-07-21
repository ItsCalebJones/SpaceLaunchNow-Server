# Runbook: Remote Diagnostics Control (per-user Datadog logging)

**Purpose:** Pull full-fidelity Datadog logs from ONE specific user's device — typically a
"notifications not working" support case we can't reproduce — without shipping a build or
asking the user to change settings. Also provides a global lever for the Datadog log
sample rate.

**Mechanism:** The KMP app (Android + iOS, from the build containing
`feat(logging): remotely control per-user diagnostics via Firebase Remote Config`) reads a
Firebase Remote Config JSON key `diagnostics_config`, matches the device's RevenueCat App
User ID against an override list, and applies a Datadog sample rate and/or diagnostic
level (`OFF` / `STANDARD` / `VERBOSE`). Client implementation lives in
`SpaceLaunchNow-KMP`: `util/logging/RemoteDiagnostics.kt`, `RemoteDiagnosticsController.kt`;
design docs: `docs/logging/REMOTE_LOG_SAMPLING_SPEC.md`, `specs/016-remote-diagnostics-control/`.

---

## 1. Get the target's RevenueCat App User ID

Any of:

- **Datadog:** logs from the device carry `rc_user_id` as a log attribute and `@usr.id`
  in user context (e.g. filter Logs by the user's error, inspect either field).
- **Diagnostics report:** the user pastes "Copy diagnostics report" output in a support
  email; combine with Datadog to resolve the id if needed.
- **RevenueCat dashboard:** look up the customer; use the **App User ID** shown there
  (often `$RCAnonymousID:...`).

⚠️ Anonymous ids (`$RCAnonymousID:...`) **rotate on reinstall or logout**. If the user
reinstalls mid-investigation, the override silently stops matching — get the new id.

## 2. Publish the override

Firebase console → project **Space Launch Now** → **Remote Config** → parameter
`diagnostics_config` (create it as a String/JSON parameter if absent) → set value:

```json
{
  "version": 1,
  "default_sample_rate": 100,
  "overrides": [
    {
      "match": { "rc_user_id": "$RCAnonymousID:PASTE-ID-HERE" },
      "sample_rate": 100,
      "diagnostic_level": "VERBOSE",
      "expires_at": "2026-08-01T00:00:00Z"
    }
  ]
}
```

**Validate the JSON before publishing** (paste into any JSON validator). A malformed
value is silently ignored by every client — the config just does nothing, with no error
surfaced anywhere.

Then click **Publish changes**.

### Field reference

| Field | Required | Notes |
|---|---|---|
| `version` | yes | Must be exactly `1`; any other value → entire config ignored |
| `default_sample_rate` | no | 0–100; applies to **every install** with no matching override — this is the global Datadog cost lever, treat with care |
| `overrides[]` | no | First matching, non-expired entry wins |
| `match.rc_user_id` | yes (per entry) | Exact raw RC App User ID |
| `sample_rate` | no | 0–100 (coerced); omit to leave sampling at the default/local value |
| `diagnostic_level` | no | `OFF` \| `STANDARD` \| `VERBOSE` (exact spelling; unknown → ignored) |
| `expires_at` | recommended | RFC-3339 UTC (`2026-08-01T00:00:00Z`). Expired or malformed date → entry ignored. **Always set this** — a few days out |

### What each level does on the device

| Level | Datadog consent | Uploads |
|---|---|---|
| `OFF` | not granted | nothing |
| `STANDARD` | granted | warn/error + the once-per-launch `Push registration summary` |
| `VERBOSE` | granted | debug and up (full firehose) — this is what you want for delivery debugging |

## 3. Wait for propagation, then verify

- **Running app:** re-checks every **6 hours** (non-forced fetch, ≤1h Firebase cache on
  top → worst case ~7h).
- **Cold start:** force-refreshes immediately → **relaunching the app picks it up right
  away**. If the user is responsive, "kill and reopen the app" is the fast path.

Verify in **Datadog → Logs**, filtered to the app service:

```
@usr.id:"$RCAnonymousID:PASTE-ID-HERE"
```
or `@rc_user_id:"..."`. Two positive signals:

1. The client logs `Remote diagnostics override applied: sampleRate=..., level=...`
   (info) once the override lands (visible when the applied level uploads info, i.e. VERBOSE).
2. `Push registration summary` lines with `push.*` attributes on each launch; at VERBOSE,
   debug-level `NotificationWorker` / topic-subscription logs appear.

## 4. Revert

Remove the override entry (or the whole parameter value) and **Publish** — or just let
`expires_at` lapse. The device reverts to the **user's own** diagnostic level and the
local sample rate automatically; their original setting is stored separately and is never
overwritten.

## Built-in safety nets (why you can't break much)

- **72h backstop:** a remote level override self-destructs 72h after the device last
  successfully re-asserted it — a forgotten config entry cannot leave a device verbose
  forever.
- **Fail-safe parsing:** malformed JSON / unknown `version` / unknown level / bad date →
  no behavior change (device uses local settings). Fetch failure (offline) → keeps the
  last-applied override until the backstop.
- **User's choice preserved:** remote state lives in separate storage keys; clearing the
  override restores whatever the user had picked.
- **Sample rates hard-coerced to 0–100.**

## Known limitations / gotchas

| Symptom | Cause / fix |
|---|---|
| No logs after publishing | App build predates the feature; user hasn't relaunched (≤7h background latency); anonymous RC id rotated (reinstall) — re-check the id; JSON invalid (validate + republish) |
| Logs exist but can't filter by user | Device predates the `rc_user_id` attribution build; RC id resolves a few seconds into launch, so the first seconds of a cold start may lack it |
| Override stopped after ~3 days | 72h backstop fired because the device couldn't re-assert (offline / app unused). Entry still published → next launch re-applies |
| Want a specific user at `OFF` silenced less / more | `diagnostic_level: "OFF"` in an override force-disables uploads for that user — also works as a per-user kill switch |
| Global spend spike | Check `default_sample_rate` — it applies to every install; lower it or remove it (devices fall back to local slider, default 100, gated by each user's consent level) |

**Consent note:** a `diagnostic_level` override flips Datadog consent ON for that device
even if the user chose Off. Use it only for users actively engaged in a support
conversation (their bug report is the ask), keep `expires_at` tight, and prefer
`STANDARD` unless you truly need the firehose.
