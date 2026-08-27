# V5-037A — GOLD Real-Yield Directional-Delivery Mechanism Contract

Status: `PREREGISTERED / DATA-QUALIFICATION NEXT`
Date: `2026-08-27`
Strategy authority: `NONE`
Production authority: `NONE`
Parent decision: `D-184`

## 1. Research question

Does the most recently and causally known change in the US 10-year TIPS real yield condition the next complete GOLD broker-day directional-delivery distribution in the economically expected inverse direction?

This is an external-state mechanism test, not an Entry test.

No Entry, SL, TP, partial, BE, trailing stop or sizing rule is authorized in V5-037A.

## 2. Source / mechanism hypothesis

Economic hypothesis:
- gold has no coupon/cash yield;
- higher real sovereign yields can raise the opportunity cost of holding gold;
- lower real yields can reduce that opportunity cost;
- the relation is not assumed stationary and may be dominated by other gold drivers.

Frozen directional hypothesis:

```text
real-yield change < 0  -> GOLD pressure direction LONG
real-yield change > 0  -> GOLD pressure direction SHORT
real-yield change = 0  -> no observation
```

No magnitude threshold is permitted.

Opposite thesis:
The inverse relation is too unstable/noisy at this horizon and does not condition next-day delivery better than its paired opposite direction or a stale-state placebo.

## 3. Data

### GOLD

Discovery market only:

```text
GOLD#
2023
M1 OHLC + recorded spread
same existing broker/feed development data
```

2024 and 2025 are closed during Stage 1 discovery.
GOLD# 2021 remains untouched.

### Real yield

Series:

```text
DFII10
Market Yield on U.S. Treasury Securities at 10-Year Constant Maturity,
Inflation-Indexed
Federal Reserve H.15
```

Point-in-time requirement:
- prefer ALFRED release-dated/vintage data or a Federal Reserve H.15 release archive;
- map each observation to the actual release date on which it became public;
- do not infer same-day availability from the FRED observation date;
- if only current revised history without defensible release availability is available, claim-grade Stage 1 must not run.

Federal Reserve H.15 is posted Monday-Friday at 4:15pm ET; recent release tables show the latest observation is normally the prior business day.

## 4. Conservative causal activation

To avoid broker-timezone ambiguity, the real-yield change released on Federal release date `D` becomes eligible only for the **first complete broker calendar day strictly after D**.

The remainder of release date D is discarded.

For each eligible broker day:
1. take the latest real-yield observation known under the release-date ledger;
2. compare it with the immediately prior known observation;
3. freeze the pressure direction from the sign rule above;
4. never revise that day's state later.

This deliberately delays information rather than risk look-ahead.

## 5. Frozen observation geometry

For each eligible broker day `t`:

Scale is the full high-low range of broker day `t-1`, known before day `t` begins:

```text
scale_t = prior_day_high - prior_day_low
```

If scale <= 0 or the prior day is unavailable, skip.

At day `t` open, measure through the complete day:

```text
signed_close_r = pressure_direction * (day_close - day_open) / scale_t

pressure_mfe_r = maximum favorable excursion from day_open
                 in pressure direction / scale_t

opposite_mfe_r = maximum excursion from day_open
                 against pressure direction / scale_t

excursion_advantage_r = pressure_mfe_r - opposite_mfe_r
```

These are mechanism observables, not trade P&L.

No clipping and no target threshold.

## 6. Frozen controls

### C1 — paired opposite-direction control

On the same day and same prices, evaluate the opposite direction.

Primary paired interpretation is captured by `excursion_advantage_r` and `signed_close_r`; do not create a separate optimized direction model.

### C2 — one-release stale placebo

Repeat the state assignment using the prior release's real-yield change instead of the freshest causally available change.

The fresh state should be more informative than the stale state if the measured relation is genuinely tied to current real-yield state rather than a slow incidental correlation.

### C3 — prior GOLD day direction confounder

Record the sign of the previous complete broker day's open-to-close return.

Report macro-pressure alignment vs disagreement with prior GOLD direction, but do not filter either group.

Purpose: test whether the result is merely prior-day price momentum wearing a macro label.

## 7. Stage 1 — 2023 discovery decision

Report:
- N;
- mean and median `signed_close_r`;
- mean and median `excursion_advantage_r`;
- pressure/opposite MFE distributions;
- H1-2023 and H2-2023 separately;
- LONG-pressure and SHORT-pressure separately;
- fresh vs stale-placebo comparison;
- prior-GOLD alignment/disagreement descriptively.

No p-value mining and no threshold selection.

Classification `MECHANISM SUPPORT FOR VALIDATION` requires all of:

```text
pooled mean signed_close_r                 > 0
pooled median signed_close_r               > 0
pooled median excursion_advantage_r        > 0
H1 median signed_close_r                   > 0
H2 median signed_close_r                   > 0
H1 median excursion_advantage_r            > 0
H2 median excursion_advantage_r            > 0
fresh mean signed_close_r                  > stale-placebo mean
fresh median excursion_advantage_r         > stale-placebo median
```

These are sign/order gates, not fitted magnitude thresholds.

If any gate fails, V5-037A closes without Entry construction. Do not rescue by yield-change magnitude, month, session, direction, or a second macro variable.

## 8. Conditional Stage 2 — frozen mechanism validation

Only if Stage 1 passes:
- freeze the exact release mapping, direction rule, day clock and metrics;
- open GOLD# 2024 and 2025;
- run unchanged;
- require pooled and each year to preserve positive median `signed_close_r` and positive median `excursion_advantage_r`;
- report directions separately;
- no threshold rescue.

This remains mechanism validation, not strategy validation.

## 9. What may happen after a successful V5-037A

Only after Stage 2 support may V5-037B ask how GOLD price itself confirms that the external pressure is being accepted and whether an Entry + structural invalidation + lifecycle can satisfy D-180:

```text
realized positive-trade rate >= 50%
average positive NET R       >= 2R
cost-adjusted EV             > 0
```

V5-037A success alone creates no trade authority.

## 10. Hard stops

- no First Cross reuse/rescue;
- no V3 Root/Sweep/CHoCH/FVG import as privileged Entry authority;
- no yield-change magnitude threshold;
- no month/session filter;
- no direction veto;
- no H.10 daily look-ahead;
- no 2024/2025 opening before Stage-1 classification is frozen;
- no GOLD# 2021 inspection;
- no production EA change.
