# Break-glass copy of django-launch-library

`fetch_ll_package.py` copies the version pinned in `poetry.lock` into the
private DigitalOcean Space `sln-break-glass`. It stores two copies:

- `published/`: the files exactly as the TSD index serves them. Each file
  is checked against its sha256 in `poetry.lock` before upload.
- `rebuilt/`: files built from the LaunchLibrary-API tag `v21.73.2`, passed
  with `--rebuild-dir`. Rebuilt bytes differ from the published ones
  (line endings in the wheel), so compare by content, not by hash.

Each folder gets a `SHA256SUMS` file in `sha256sum` format.

## Layout

```
s3://sln-break-glass/ll-package/<version>/published/<files> + SHA256SUMS
s3://sln-break-glass/ll-package/<version>/rebuilt/<files>   + SHA256SUMS
```

## Environment variables

Index (TSD private PyPI), same names as `docker/.env`:

- `POETRY_HTTP_BASIC_TSD_USERNAME`
- `POETRY_HTTP_BASIC_TSD_PASSWORD`

Spaces (only for a real upload, not `--dry-run`):

- `SLN_BREAK_GLASS_ACCESS_KEY_ID`: Vault `secret/sln-break-glass`, key `aws-access-key-id`
- `SLN_BREAK_GLASS_SECRET_ACCESS_KEY`: Vault `secret/sln-break-glass`, key `aws-secret-access-key`
- `SLN_BREAK_GLASS_ENDPOINT` (optional, default `https://nyc3.digitaloceanspaces.com`)
- `SLN_BREAK_GLASS_REGION` (optional, default `us-east-1`)

Never put the values in a file or on a command line that is logged.

## Run

From the repo root. `boto3` is not needed for `--dry-run`. The real
upload uses `boto3` 1.39.12, the version already pinned in `poetry.lock`.

```sh
# Plan only: downloads and verifies, uploads nothing
uv run --no-project --with boto3==1.39.12 python scripts/break_glass/fetch_ll_package.py \
  --lock poetry.lock --rebuild-dir <rebuild/dist> --dry-run

# Upload both copies
uv run --no-project --with boto3==1.39.12 python scripts/break_glass/fetch_ll_package.py \
  --lock poetry.lock --rebuild-dir <rebuild/dist>
```

Options: `--download-dir` (default: a new temp folder), `--bucket`,
`--prefix` (default `ll-package/`), `--overwrite` (replace existing keys;
the default refuses).

The rebuilt copy: `git -C <LaunchLibrary-API> archive v21.73.2 | tar -x -C <dir>`,
then `uv build --out-dir <dir>/dist` in the exported `<dir>`.

## Checks after upload

List the prefix with the same env vars set:

```sh
uv run --no-project --with boto3==1.39.12 python -c "
import boto3, os
s3 = boto3.client('s3', endpoint_url=os.environ.get('SLN_BREAK_GLASS_ENDPOINT', 'https://nyc3.digitaloceanspaces.com'),
                  region_name=os.environ.get('SLN_BREAK_GLASS_REGION', 'us-east-1'),
                  aws_access_key_id=os.environ['SLN_BREAK_GLASS_ACCESS_KEY_ID'],
                  aws_secret_access_key=os.environ['SLN_BREAK_GLASS_SECRET_ACCESS_KEY'])
for o in s3.list_objects_v2(Bucket='sln-break-glass', Prefix='ll-package/')['Contents']:
    print(o['Key'], o['Size'])
"
```
