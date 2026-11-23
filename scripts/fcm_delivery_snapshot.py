#!/usr/bin/env python
"""Snapshot the FCM Data API to measure the V5 to V6 gate for dual-send retirement.

Read-only. Run it by hand from a local checkout; it is never deployed.

    python scripts/fcm_delivery_snapshot.py                 # live, Android, last window
    python scripts/fcm_delivery_snapshot.py --markdown      # add the doc table row
    python scripts/fcm_delivery_snapshot.py --input resp.json   # parse a saved response

Live mode needs `gcloud` logged in to the `space-launch-now` project. The token is
read from `gcloud auth print-access-token` and is never printed.

Gate (Contracts notifications/plans/2026-08-30-android-push-delivery-followups-spec.md, D13):
V5 subscribers <= 5 % of V6 subscribers for 14 consecutive days. For one send,
`countMessagesAccepted` on its label is the number of devices subscribed to that
topic, so V5 = the `v5_android_<id>` count and V6 = the sum over the six
`v6_<class>_<id>` labels (all, flex, strict, each with a `_w` webcast variant).
FCM returns `data: {}` for labels below its reporting threshold; those count as
zero, which understates V6 and so overstates the ratio (the safe direction).
A label that carries several messages in one day (one launch, several reminder
types) adds them up, so a day's counts are messages, not devices. V5 sends every
type to every device and V6 sends each type only to subscribers of it, so on
such days V5/V6 reads high. It is a conservative proxy: a day that passes at
5 % is safe, a day that fails by a wide margin is not proof of the device ratio.

The API keeps about 7 days. A 14-day streak therefore comes from chaining
snapshots: run at least weekly and keep each row (see
docs/runbooks/v5-retirement-gate.md).

iOS is not covered: the FCM Data API only serves Android apps. The D14 health
gate (clients that never finished the changeover) comes from client logs, not
from this script.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, date, datetime

PROJECT = "space-launch-now"
ANDROID_APP_ID = "1:610310574961:android:4553f5c8ecd77279"
API_ROOT = "https://fcmdata.googleapis.com/v1beta1"
GATE_RATIO = 0.05
GATE_DAYS = 14

# `v6_<class>[_w]_<id>` for launch sends; `v6_<platform>_<kind>_<id>` for broadcasts.
_V6_CLASS = re.compile(r"^v6_(?:all|flex|strict)(?:_w)?_(?P<key>.+)$")
_V6_BROADCAST = re.compile(r"^v6_android_(?P<key>.+)$")
_V5 = re.compile(r"^v5_android_(?P<key>.+)$")


def classify_label(label: str) -> tuple[str, str] | None:
    """Return ("v5" | "v6", send key) for an Android label, else None.

    The send key ties a V5 label to the V6 labels of the same send: the launch
    UUID, or `<kind>_<id>` for broadcasts such as event and custom pushes.
    """
    match = _V5.match(label)
    if match:
        return "v5", match["key"]
    match = _V6_CLASS.match(label) or _V6_BROADCAST.match(label)
    if match:
        return "v6", match["key"]
    return None


def accepted(row: dict) -> int:
    """Messages FCM accepted for a row; 0 when `data` is empty (below threshold)."""
    return int(row.get("data", {}).get("countMessagesAccepted", 0))


def _row_day(row: dict) -> date:
    d = row["date"]
    return date(d["year"], d["month"], d["day"])


@dataclass
class DayStats:
    day: date
    v5: int = 0
    v6: int = 0
    paired_sends: int = 0
    empty_v6_labels: int = 0
    # Weighted by V5 accepted count: [sum(priorityLowered * accepted), sum(accepted)].
    _lowered: list = field(default_factory=lambda: [0.0, 0])

    @property
    def ratio(self) -> float | None:
        return self.v5 / self.v6 if self.v6 else None

    @property
    def passes(self) -> bool:
        return self.ratio is not None and self.ratio <= GATE_RATIO

    @property
    def v5_priority_lowered(self) -> float | None:
        weighted, total = self._lowered
        return weighted / total if total else None


def aggregate(rows: list[dict]) -> list[DayStats]:
    """Roll rows up to one DayStats per day, oldest first.

    Only sends that have a V5 label on that day count: V6-only sends (no V5
    leg to compare) would inflate the denominator. Days with no labelled rows
    are skipped.
    """
    sends: dict[date, dict[str, dict]] = defaultdict(lambda: defaultdict(lambda: {"v5": [], "v6": []}))
    for row in rows:
        label = row.get("analyticsLabel")
        kind = classify_label(label) if label else None
        if kind:
            side, key = kind
            sends[_row_day(row)][key][side].append(row)

    days = []
    for day in sorted(sends):
        stats = DayStats(day=day)
        for parts in sends[day].values():
            if not parts["v5"]:
                continue
            stats.paired_sends += 1
            for row in parts["v5"]:
                count = accepted(row)
                stats.v5 += count
                lowered = row.get("data", {}).get("messageInsightPercents", {}).get("priorityLowered")
                if lowered is not None and count:
                    stats._lowered[0] += lowered * count
                    stats._lowered[1] += count
            for row in parts["v6"]:
                count = accepted(row)
                stats.v6 += count
                stats.empty_v6_labels += count == 0
        if stats.paired_sends:
            days.append(stats)
    return days


def trailing_pass_streak(days: list[DayStats]) -> int:
    """Consecutive passing calendar days ending at the newest day in `days`."""
    streak = 0
    previous = None
    for stats in reversed(days):
        if not stats.passes or (previous and (previous - stats.day).days != 1):
            break
        streak += 1
        previous = stats.day
    return streak


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.1f}%"


def format_report(days: list[DayStats]) -> str:
    lines = [f"{'day':<12}{'sends':>6}{'V5':>9}{'V6':>9}{'V5/V6':>9}{'empty V6':>10}{'V5 prioLow':>12}  gate"]
    for s in days:
        lowered = "n/a" if s.v5_priority_lowered is None else f"{s.v5_priority_lowered:.1f}%"
        lines.append(
            f"{s.day.isoformat():<12}{s.paired_sends:>6}{s.v5:>9}{s.v6:>9}{_pct(s.ratio):>9}"
            f"{s.empty_v6_labels:>10}{lowered:>12}  {'pass' if s.passes else 'FAIL'}"
        )
    streak = trailing_pass_streak(days)
    lines.append("")
    lines.append(
        f"Gate (V5 <= {GATE_RATIO:.0%} of V6, {GATE_DAYS} consecutive days): "
        f"{streak} passing day(s) at the end of this window; {'MET' if streak >= GATE_DAYS else 'NOT MET'}."
    )
    lines.append("Counts are messages accepted per label and day (several sends add up), not devices.")
    lines.append("Health gate D14 (no device with an incomplete changeover for 7 days): not measured here.")
    return "\n".join(lines)


def markdown_row(days: list[DayStats], snapshot: date) -> str:
    """One `Retirement status` table row for the whole window."""
    if not days:
        return f"| {snapshot.isoformat()} | no data | | | | | | |"
    v5 = sum(s.v5 for s in days)
    v6 = sum(s.v6 for s in days)
    ratios = [s.ratio for s in days if s.ratio is not None]
    weighted = sum(s._lowered[0] for s in days)
    total = sum(s._lowered[1] for s in days)
    lowered = "n/a" if not total else f"{weighted / total:.1f}%"
    return (
        f"| {snapshot.isoformat()} | {days[0].day.isoformat()} to {days[-1].day.isoformat()} ({len(days)} d) "
        f"| {v5} | {v6} | {_pct(v5 / v6 if v6 else None)} "
        f"| {_pct(min(ratios)) if ratios else 'n/a'} to {_pct(max(ratios)) if ratios else 'n/a'} "
        f"| {lowered} | {trailing_pass_streak(days)} |"
    )


MARKDOWN_HEADER = (
    "| Snapshot | Window | V5 accepted | V6 accepted | V5/V6 | Daily range | V5 priorityLowered "
    "| Passing days at window end |\n"
    "|---|---|---|---|---|---|---|---|"
)


def _access_token() -> str:
    gcloud = shutil.which("gcloud")
    if not gcloud:
        raise SystemExit("gcloud not found on PATH; install it and run `gcloud auth login`.")
    result = subprocess.run([gcloud, "auth", "print-access-token"], capture_output=True, text=True, timeout=60)
    token = result.stdout.strip()
    if result.returncode or not token:
        raise SystemExit("gcloud has no valid login; run `gcloud auth login` and retry.")
    return token


def fetch_rows(app_id: str = ANDROID_APP_ID, page_size: int = 200) -> list[dict]:
    """Read every `deliveryData` page for the app. GET only."""
    token = _access_token()
    rows: list[dict] = []
    page_token = ""
    while True:
        query = {"pageSize": page_size}
        if page_token:
            query["pageToken"] = page_token
        url = f"{API_ROOT}/projects/{PROJECT}/androidApps/{app_id}/deliveryData?{urllib.parse.urlencode(query)}"
        request = urllib.request.Request(
            url, headers={"Authorization": f"Bearer {token}", "x-goog-user-project": PROJECT}
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = json.load(response)
        except urllib.error.HTTPError as exc:
            raise SystemExit(f"FCM Data API returned HTTP {exc.code}; check the account has FCM data access.") from exc
        rows.extend(body.get("androidDeliveryData", []))
        page_token = body.get("nextPageToken", "")
        if not page_token:
            return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--input", help="parse a saved deliveryData JSON response instead of calling the API")
    parser.add_argument("--markdown", action="store_true", help="also print the retirement-status table row")
    args = parser.parse_args(argv)

    if args.input:
        with open(args.input, encoding="utf-8") as handle:
            rows = json.load(handle).get("androidDeliveryData", [])
    else:
        rows = fetch_rows()

    days = aggregate(rows)
    print(format_report(days))
    if args.markdown:
        print()
        print(MARKDOWN_HEADER)
        print(markdown_row(days, datetime.now(UTC).date()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
