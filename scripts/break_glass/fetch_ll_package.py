#!/usr/bin/env python3
"""Mirror the pinned django-launch-library package into the sln-break-glass Space.

Steps:
  1. Read the pinned version, file names and sha256 hashes from poetry.lock.
  2. Download those files from the private TSD index (credentials from env).
  3. Verify every downloaded file against the lock hash. Abort on mismatch.
  4. Optionally add locally rebuilt artifacts from --rebuild-dir.
  5. Upload to s3://<bucket>/<prefix><version>/published/ and .../rebuilt/,
     each with a SHA256SUMS file.

Credentials come only from environment variables. The script never prints
their values.

See README.md in this folder for the env vars and the run command.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import os
import pathlib
import sys
import tomllib
import urllib.parse
import urllib.request
from dataclasses import dataclass

PACKAGE = "django-launch-library"
DEFAULT_BUCKET = "sln-break-glass"
DEFAULT_PREFIX = "ll-package/"
DEFAULT_ENDPOINT = "https://nyc3.digitaloceanspaces.com"
DEFAULT_REGION = "us-east-1"
# The TSD index sits behind Cloudflare, which rejects the default urllib agent.
HTTP_USER_AGENT = "pip/24.0"
CHUNK = 1024 * 1024


@dataclass(frozen=True)
class Artifact:
    name: str
    sha256: str
    path: pathlib.Path
    group: str  # "published" or "rebuilt"


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


def sha256_of(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def read_lock(lock_path: pathlib.Path) -> tuple[str, str, list[tuple[str, str]]]:
    """Return (version, index_url, [(file_name, sha256), ...]) for the package."""
    with lock_path.open("rb") as handle:
        lock = tomllib.load(handle)
    for entry in lock.get("package", []):
        if entry.get("name") == PACKAGE:
            files = []
            for item in entry.get("files", []):
                algo, _, hex_digest = item["hash"].partition(":")
                if algo != "sha256":
                    fail(f"unexpected hash algorithm in lock: {algo}")
                files.append((item["file"], hex_digest))
            index_url = entry.get("source", {}).get("url", "")
            if not index_url:
                fail("poetry.lock has no [package.source] url for the package")
            return entry["version"], index_url, files
    fail(f"{PACKAGE} not found in {lock_path}")
    raise AssertionError("unreachable")


def index_credentials() -> str:
    user = os.environ.get("TSD_INDEX_USERNAME") or os.environ.get("POETRY_HTTP_BASIC_TSD_USERNAME")
    password = os.environ.get("TSD_INDEX_PASSWORD") or os.environ.get("POETRY_HTTP_BASIC_TSD_PASSWORD")
    if not user or not password:
        fail(
            "set POETRY_HTTP_BASIC_TSD_USERNAME and POETRY_HTTP_BASIC_TSD_PASSWORD "
            "(or TSD_INDEX_USERNAME / TSD_INDEX_PASSWORD)"
        )
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    return f"Basic {token}"


def http_get(url: str, auth: str) -> bytes:
    request = urllib.request.Request(
        url, headers={"Authorization": auth, "User-Agent": HTTP_USER_AGENT, "Accept": "text/html"}
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        return response.read()


def download_published(
    index_url: str, files: list[tuple[str, str]], dest: pathlib.Path
) -> list[Artifact]:
    """Download each locked file from the index and verify its hash."""
    import html as html_lib
    import re

    auth = index_credentials()
    project_url = index_url.rstrip("/") + "/" + PACKAGE + "/"
    page = http_get(project_url, auth).decode("utf-8", "replace")
    links = {
        html_lib.unescape(text).strip(): html_lib.unescape(href)
        for href, text in re.findall(r'<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', page)
    }

    artifacts: list[Artifact] = []
    for name, expected in files:
        if name not in links:
            fail(f"{name} is not listed on the index page")
        url = urllib.parse.urljoin(project_url, links[name]).split("#", 1)[0]
        target = dest / name
        target.write_bytes(http_get(url, auth))
        actual = sha256_of(target)
        if actual != expected:
            fail(f"hash mismatch for {name}: lock {expected}, downloaded {actual}")
        print(f"verified published {name} sha256 matches poetry.lock")
        artifacts.append(Artifact(name, actual, target, "published"))
    return artifacts


def collect_rebuilt(rebuild_dir: pathlib.Path, version: str) -> list[Artifact]:
    """Pick up the locally rebuilt wheel and sdist for this version."""
    stem = PACKAGE.replace("-", "_") + "-" + version
    found = sorted(
        p for p in rebuild_dir.iterdir()
        if p.is_file() and (p.name.startswith(stem + ".") or p.name.startswith(stem + "-"))
        and (p.name.endswith(".whl") or p.name.endswith(".tar.gz"))
    )
    if not found:
        fail(f"no {stem} wheel or sdist in {rebuild_dir}")
    return [Artifact(p.name, sha256_of(p), p, "rebuilt") for p in found]


def sums_file(artifacts: list[Artifact], dest: pathlib.Path) -> pathlib.Path:
    """Write a SHA256SUMS file in sha256sum format for one group."""
    target = dest / "SHA256SUMS"
    lines = [f"{a.sha256}  {a.name}" for a in artifacts]
    target.write_text("\n".join(lines) + "\n", encoding="ascii")
    return target


def plan_uploads(
    version: str, prefix: str, artifacts: list[Artifact], sums_dir: pathlib.Path
) -> list[tuple[pathlib.Path, str]]:
    """Return (local_path, s3_key) pairs for every object to upload."""
    plan: list[tuple[pathlib.Path, str]] = []
    for group in ("published", "rebuilt"):
        members = [a for a in artifacts if a.group == group]
        if not members:
            continue
        group_dir = sums_dir / group
        group_dir.mkdir(parents=True, exist_ok=True)
        sums = sums_file(members, group_dir)
        base = f"{prefix}{version}/{group}/"
        for artifact in members:
            plan.append((artifact.path, base + artifact.name))
        plan.append((sums, base + "SHA256SUMS"))
    return plan


def make_s3_client():
    try:
        import boto3
    except ImportError:
        fail(
            "boto3 is missing. Run: uv run --no-project --with boto3==1.39.12 "
            "python scripts/break_glass/fetch_ll_package.py ..."
        )
    key_id = os.environ.get("SLN_BREAK_GLASS_ACCESS_KEY_ID")
    secret = os.environ.get("SLN_BREAK_GLASS_SECRET_ACCESS_KEY")
    if not key_id or not secret:
        fail("set SLN_BREAK_GLASS_ACCESS_KEY_ID and SLN_BREAK_GLASS_SECRET_ACCESS_KEY")
    return boto3.client(
        "s3",
        endpoint_url=os.environ.get("SLN_BREAK_GLASS_ENDPOINT", DEFAULT_ENDPOINT),
        region_name=os.environ.get("SLN_BREAK_GLASS_REGION", DEFAULT_REGION),
        aws_access_key_id=key_id,
        aws_secret_access_key=secret,
    )


def object_exists(client, bucket: str, key: str) -> bool:
    from botocore.exceptions import ClientError

    try:
        client.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as error:
        if error.response.get("Error", {}).get("Code") in ("404", "NoSuchKey", "NotFound"):
            return False
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--lock", type=pathlib.Path, default=pathlib.Path("poetry.lock"),
                        help="path to SLN-Server poetry.lock (default: ./poetry.lock)")
    parser.add_argument("--download-dir", type=pathlib.Path,
                        help="where published files are downloaded (default: a new temp dir)")
    parser.add_argument("--rebuild-dir", type=pathlib.Path,
                        help="folder with locally rebuilt wheel/sdist to include under rebuilt/")
    parser.add_argument("--bucket", default=DEFAULT_BUCKET)
    parser.add_argument("--prefix", default=DEFAULT_PREFIX, help="key prefix, must end with /")
    parser.add_argument("--overwrite", action="store_true",
                        help="replace objects that already exist (default: refuse)")
    parser.add_argument("--dry-run", action="store_true",
                        help="download and verify, then print the upload plan; no uploads")
    args = parser.parse_args()

    if not args.prefix.endswith("/"):
        fail("--prefix must end with /")

    import tempfile

    version, index_url, files = read_lock(args.lock)
    print(f"pinned {PACKAGE} {version}: {len(files)} file(s) in poetry.lock")

    download_dir = args.download_dir or pathlib.Path(tempfile.mkdtemp(prefix="ll-package-"))
    download_dir.mkdir(parents=True, exist_ok=True)
    artifacts = download_published(index_url, files, download_dir)

    if args.rebuild_dir:
        artifacts += collect_rebuilt(args.rebuild_dir, version)

    sums_dir = pathlib.Path(tempfile.mkdtemp(prefix="ll-package-sums-"))
    plan = plan_uploads(version, args.prefix, artifacts, sums_dir)

    print(f"upload plan to s3://{args.bucket}/ ({len(plan)} objects):")
    for local, key in plan:
        print(f"  {key}  <- {local.name}  ({local.stat().st_size} bytes)")

    if args.dry_run:
        print("dry run: nothing uploaded")
        return

    client = make_s3_client()
    if not args.overwrite:
        for _, key in plan:
            if object_exists(client, args.bucket, key):
                fail(f"s3://{args.bucket}/{key} already exists; rerun with --overwrite to replace it")
    for local, key in plan:
        client.upload_file(str(local), args.bucket, key)
        print(f"uploaded s3://{args.bucket}/{key}")


if __name__ == "__main__":
    main()
