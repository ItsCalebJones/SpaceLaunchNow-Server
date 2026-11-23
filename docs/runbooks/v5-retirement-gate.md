# Runbook: V5 dual-send retirement gate (Android)

**Purpose:** Measure whether the Android V5 topic broadcast can be retired. Spec: Contracts
`notifications/plans/2026-08-30-android-push-delivery-followups-spec.md` (S4, D12 to D16).

## Gate

Android retires when both hold:

1. **Adoption (D13):** V5 subscribers are at most 5 % of V6 subscribers for 14 consecutive days.
2. **Health (D14):** 0 identifiable devices with an incomplete V6 changeover over 7 days
   (`push_summary` with `push.changeover_complete:false`, from client logs). The script does not measure this.

Retirement is per platform (D12). iOS is not covered here: the FCM Data API serves Android apps only
(Tasks#38 owns iOS).

## Take a snapshot

Needs `gcloud` logged in to project `space-launch-now`. Read-only; never deployed.

```sh
python scripts/fcm_delivery_snapshot.py --markdown
```

The API keeps about 7 days, so run it at least weekly and append the printed row below. Each row
names its window, so the streak chains across rows. Data lags 5 to 7 days.

Reading the output: counts are messages accepted per label and day. A label that carries several
sends in a day adds them up, and V5 sends every type to every device while V6 sends each type only to
subscribers of it, so V5/V6 reads high on those days. A pass at 5 % is safe; a fail by a wide margin is
not proof of the device ratio. `empty V6` counts V6 labels FCM returned as `data: {}` (below its
reporting threshold, counted as zero, which also overstates the ratio).

Open question Q2 (empty `v6_*` labels): as of 2026-11-23 the `v6_all_*`, `v6_flex_*` and
`v6_strict_*` labels report; the webcast variants (`v6_*_w_*`) come back empty.

## Retirement status

| Snapshot | Window | V5 accepted | V6 accepted | V5/V6 | Daily range | V5 priorityLowered | Passing days at window end |
|---|---|---|---|---|---|---|---|
| 2026-11-23 | 2026-11-12 to 2026-11-17 (3 d) | 84506 | 58132 | 145.4% | 94.4% to 209.4% | 5.5% | 0 |
