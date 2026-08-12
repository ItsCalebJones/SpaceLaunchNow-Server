# Runbook: Static Assets (CSS/JS on DigitalOcean Spaces)

**Purpose:** Explain why a newly added CSS/JS file can render a correct-looking page while
404'ing in the browser, and how to publish one. Read this if you added a file under
`src/static/` and it is not loading in staging or production.

**Mechanism:** Outside local development the site does not serve static files itself. Django
generates `{% static %}` URLs from `STATIC_URL`, which points at a DigitalOcean Spaces
bucket, and the files must be uploaded there separately by `collectstatic`. The two halves
are configured independently, which is what makes the failure quiet.

| Environment | Bucket | Selected by |
|---|---|---|
| Local | filesystem | `USE_LOCAL_STORAGE=true` |
| Staging | `thespacedevs-dev` | `STORAGE_BUCKET_NAME` |
| Production | `thespacedevs` | `STORAGE_BUCKET_NAME` |

---

## 1. The Django 5.1 trap (fixed 2026-08-12 — do not reintroduce)

`DEFAULT_FILE_STORAGE` and `STATICFILES_STORAGE` were **removed in Django 5.1**. Setting them
raises nothing — Django ignores them and falls back to local filesystem storage. Because
`STATIC_URL` is configured separately, the app kept emitting correct Spaces URLs while
`collectstatic` wrote to local disk, so uploads silently stopped. Assets already in the
bucket kept working, which hid it; only *newly added* files 404'd.

Storage backends are now configured via `STORAGES` in `src/spacelaunchnow/settings/__init__.py`.
`src/spacelaunchnow/tests_storages.py` asserts the **resolved** backend class, so the same
silent fallback cannot return.

If `collectstatic` ever fails with *"You're using the staticfiles app without having set the
STATIC_ROOT setting"*, that is this bug: staticfiles resolved to the local backend.

## 2. Publish a new or changed static file

Deploying the image does **not** upload static files. After the deploy carrying your file is
live, run `collectstatic` from the running pod — it already holds the bucket credentials and
runs exactly the deployed commit:

```bash
# staging (namespace sln-dev)
POD=$(kubectl get pods -n sln-dev -o name | grep staging-spacelaunchnow-web | head -1)
kubectl exec -n sln-dev "$POD" -- python manage.py collectstatic --noinput
```

For production use namespace `sln-prod` and the `sln-production-spacelaunchnow-web` pod.

**Never pass `--clear`** — it deletes the bucket contents before uploading.

## 3. Verify

Confirm the asset is actually served, not just referenced:

```bash
kubectl exec -n sln-dev "$POD" -- python -c "
import urllib.request
u='https://thespacedevs-dev.nyc3.digitaloceanspaces.com/static/home/material_kit/js/<file>.js'
print(urllib.request.urlopen(u, timeout=20).status)"
```

A `200` means published. A `404` means `collectstatic` did not upload it — re-check section 1
before re-running.
