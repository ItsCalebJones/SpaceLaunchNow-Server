# Runbook: Break-glass (package index or database login gone)

**Purpose:** Get SpaceLaunchNow-Server built, shipped and restored when you lose the private
LaunchLibrary (LL) package index, or the login to the LL database. Read the scenario that
matches. Do the steps in order.

**Scope:** This page does not restore LL's own data. LL restores its own tables by its own
runbook. The Terminus project removes both dependencies later. Until then, this page is the
fallback.

| What is lost | Go to |
|---|---|
| The TSD package index (no `django-launch-library` download) | Scenario 1 |
| The LL database login (SLN cannot read or write its tables) | Scenario 2 |

You need the Spaces keys for both scenarios. They are in Vault at `secret/sln-break-glass`
(`aws-access-key-id`, `aws-secret-access-key`). Put them in your shell, not in a file:

```sh
export AWS_ACCESS_KEY_ID=$(vault kv get -field=aws-access-key-id secret/sln-break-glass)
export AWS_SECRET_ACCESS_KEY=$(vault kv get -field=aws-secret-access-key secret/sln-break-glass)
export AWS_DEFAULT_REGION=us-east-1
```

---

## Scenario 1: the package index is gone

The bucket `sln-break-glass` holds the pinned `django-launch-library` wheel in two copies:

- `ll-package/<version>/published/`: TSD's own files. Hashes equal the ones in `poetry.lock`. Use this one.
- `ll-package/<version>/rebuilt/`: built from LL tag `v21.73.2`. Use it only if `published/` is damaged. See Known limits.

1. Read the pinned version:
   ```sh
   python3 -c 'import tomllib; print(next(p["version"] for p in tomllib.load(open("poetry.lock","rb"))["package"] if p["name"]=="django-launch-library"))'
   ```
2. Download the wheel into `vendor/` (repo root):
   ```sh
   mkdir -p vendor
   aws s3 cp s3://sln-break-glass/ll-package/<version>/published/ vendor/ --recursive --endpoint-url https://nyc3.digitaloceanspaces.com
   ```
3. Verify the hash. Every line must say `OK`:
   ```sh
   cd vendor && sha256sum -c SHA256SUMS && cd ..
   ```
4. Build the image. This file installs the wheel from `vendor/` and needs no TSD login:
   ```sh
   docker build -f docker/Dockerfile.break-glass -t sln-break-glass:local .
   ```
5. Smoke test. The first two commands must exit 0. The third must print nothing:
   ```sh
   docker run --rm sln-break-glass:local python -c "import api, configurations, bot; print('ok')"
   docker run --rm sln-break-glass:local python -m django --version
   docker run --rm sln-break-glass:local sh -c 'grep -rIl "pypi.thespacedevs" /code /code/.venv 2>/dev/null'
   ```
6. Ship the image. Normal builds run in `.github/workflows/ci.yml` and push to
   `registry.digitalocean.com/sln-prod-registry-01` (image `space-launch-now-base`). Production
   moves by `.github/workflows/promote.yml` (input: a staging tag) and the `image.tag` value in
   the GitOps repo. Push your image to that registry under a new tag, then follow the GitOps
   skill `deploying-an-image-update`. Check the exact registry path in those two files first.

**Weekly proof.** The GitHub workflow `.github/workflows/break-glass-build.yml` runs on Mondays
at 06:17 UTC and on each change to `poetry.lock`, `pyproject.toml` or the Dockerfile. Its first
job, `mirror-ll-package`, stores the pinned version in `published/` if it is not there yet (it
checks each file against `poetry.lock` first). Its second job, `break-glass-build`, runs the
steps above. It pushes no image. It uses the GitHub secrets `BREAK_GLASS_AWS_ACCESS_KEY_ID` and
`BREAK_GLASS_AWS_SECRET_ACCESS_KEY` (a CI key limited to the bucket), and `PRIVATE_USERNAME` /
`PRIVATE_PASSWORD` for the TSD index. If it is red, open the failed step:

- Fetch step fails: the TSD index is down or its login changed (this is scenario 1 starting),
  a file does not match its `poetry.lock` hash, or only some files of the version are stored.
- Download step fails: the wheel for the pinned version is missing, or the keys are wrong. See Upkeep.
- Hash step fails: the stored wheel is damaged. Upload it again with `--overwrite`.
- Build step fails: a dependency changed. Fix `docker/Dockerfile.break-glass`.

---

## Scenario 2: the database login is gone

**What the dump holds.** A CronJob in `sln-prod` runs daily at 06:30 UTC. It writes
`pg_dump --format=custom` of 30 SLN-owned tables (file `sln_own_tables.dump`), plus
`launch_flags.csv` and `event_flags.csv`, plus `SHA256SUMS`. Paths:

- `s3://sln-break-glass/dumps/daily/<YYYY-MM-DD>/`
- On the first of the month also `s3://sln-break-glass/dumps/monthly/<YYYY-MM>/`

**What it does not hold.** LL's own tables (launches, events, agencies). Restore those first,
by LL's runbook. The flag files carry only the notification flags for `api_launch` and
`api_events` rows.

**API tokens.** Tokens in `authtoken_token` are in the dump. If a dump ever leaks, treat every
token as exposed and regenerate them all.

**Restore.** Human-gated. Do not run against the live database without Caleb's approval.

1. Fetch and verify:
   ```sh
   aws s3 cp s3://sln-break-glass/dumps/daily/<DATE>/ ./restore/ --recursive --endpoint-url https://nyc3.digitaloceanspaces.com
   cd restore && sha256sum -c SHA256SUMS
   ```
2. Restore LL's data first. The `api_launch` and `api_events` rows must exist in the target
   database before step 5. Do not restore LL's tables from this dump.
3. Make the table of contents. If LL owns the `api_article*` rows, delete those lines from `toc.txt`:
   ```sh
   pg_restore -l sln_own_tables.dump > toc.txt
   ```
4. Dry run in a scratch database. Compare row counts with the live tables:
   ```sh
   createdb sln_restore_check
   pg_restore -L toc.txt --no-owner --no-acl --exit-on-error -d sln_restore_check sln_own_tables.dump
   ```
5. Live restore. Truncate the listed tables first. This destroys data and needs approval.
   `--data-only` is right because the migrated schema already exists. The database owner
   cannot use `--disable-triggers`, so the dump's own order must satisfy the foreign keys:
   ```sh
   pg_restore -L toc.txt --data-only --single-transaction --no-owner --no-acl --exit-on-error -d <db> sln_own_tables.dump
   ```
6. Restore the flags, after the LL rows exist. Save this as `flags.sql` in the restore folder:
   ```sql
   BEGIN;
   CREATE TEMP TABLE launch_flags_in (id uuid PRIMARY KEY, notifications_enabled boolean);
   \copy launch_flags_in FROM 'launch_flags.csv' CSV HEADER
   UPDATE api_launch l SET notifications_enabled = f.notifications_enabled FROM launch_flags_in f WHERE l.id = f.id;
   CREATE TEMP TABLE event_flags_in (id integer PRIMARY KEY, notifications_enabled boolean, was_notified_ten_minutes boolean, was_notified_webcast_live boolean);
   \copy event_flags_in FROM 'event_flags.csv' CSV HEADER
   UPDATE api_events e SET notifications_enabled = f.notifications_enabled, was_notified_ten_minutes = f.was_notified_ten_minutes, was_notified_webcast_live = f.was_notified_webcast_live FROM event_flags_in f WHERE e.id = f.id;
   COMMIT;
   ```
   Run it:
   ```sh
   psql -v ON_ERROR_STOP=1 -d <db> -f flags.sql
   ```
   Compare each `UPDATE n` count with the CSV line count minus one (the header). Count lines with
   `wc -l launch_flags.csv event_flags.csv`.

---

## Upkeep

- When `poetry.lock` moves to a new LL version, the `mirror-ll-package` job stores TSD's files
  for it. The `rebuilt/` copy needs the private LL repo, so build it by hand for each new
  version (from the repo root, with the `SLN_BREAK_GLASS_*` and `POETRY_HTTP_BASIC_TSD_*`
  variables set; see `scripts/break_glass/README.md`). `--skip-existing` leaves the stored
  `published/` files alone and uploads only what is missing:
  ```sh
  uv run --no-project --with boto3==1.39.12 python scripts/break_glass/fetch_ll_package.py \
    --lock poetry.lock --rebuild-dir <rebuild/dist> --skip-existing
  ```
- Retention: the dump job keeps the newest 30 folders in `dumps/daily/` and the newest 12 in
  `dumps/monthly/`, and deletes older ones after each upload. `ll-package/` is never pruned.
- Alert: `SLNBreakGlassDumpStale` fires when the dump job has had no successful run for 26 hours.
  Check the job with `kubectl -n sln-prod get cronjob,jobs -l cron=break-glass-dump` and its logs.
- Restore test: after the first dump, and after any change to the table list, restore the newest
  dump into a throwaway Postgres 18 container and compare row counts with prod
  (`scripts/break_glass/restore_test.sh`).
- Two keys, both limited to `sln-break-glass`: the dump key in Vault at `secret/sln-break-glass`
  (the CronJob reads it through an ExternalSecret; people use it for restores) and the CI key in
  the GitHub secrets `BREAK_GLASS_AWS_ACCESS_KEY_ID` / `BREAK_GLASS_AWS_SECRET_ACCESS_KEY`.
  Rotate each one on its own.

## Known limits

- The `rebuilt/` wheel has CRLF line endings, so its hashes differ from `published/`. Compare
  by content, not by hash.
- The dump and the two CSV files are separate snapshots, taken moments apart. A flag can
  differ from its table row by a few seconds of change.
- The dump is not encrypted. The bucket is private. This is a decision, not an oversight.
