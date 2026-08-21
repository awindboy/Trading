# D-146 Continuation State Audit

Date: 2026-08-21
Status: **IMPLEMENTED SHADOW MEASUREMENT / LOCAL COMPILE + PARITY PENDING**
Strategy authority: **NONE**
Implementation identity: `1.92R1L8 / CONTINUATION_STATE_AUDIT_V1_SHADOW`
Measurement logic surface: `mt5/experts/EdgeAuditV1.mqh`; EA changes are diagnostic identity only and strategy/order hooks remain unchanged
Parent evidence: `docs/ea/D145_RUNNER_GENERALIZATION_RESULTS.md`
2021: **KEEP UNTOUCHED**

## 1. Purpose

D-145 established a cross-market descriptive relationship:

> Among trades that already reached +1R, +2R runners tend to be less mature inside the current scenario-direction M30 protected-to-external range at the +1R moment.

D-146 must determine whether this is a causal market-structure mechanism or only a proxy.

The specific research question is:

> Does post-+1R M30 structure evolution explain why some trades near a mature M30 external still reach +2R, and why some trades with substantial remaining M30 room nevertheless fail before +2R?

## 2. Population

Primary D-146 population:

```text
actual filled EXTERNAL_CONTINUATION trade
+
first +1R reached before SL
```

D-146 begins only at the first exact +1R touch.

Trades that fail before +1R are not part of this continuation-state population.

Entry-survival research is a separate branch.

## 3. Observation window

For each primary trade:

```text
T0 = exact first +1R reach
T1 = exact +2R reach OR normalized-SL reach, whichever occurs first
```

D-146 tracks causal M30 structure only during `[T0, T1]`.

No arbitrary time cutoff.

If tester end occurs before terminal resolution, right-censor explicitly.

## 4. Snapshot at +1R

Reuse/freeze D-145 causal state where possible:

```text
scenario_id
scope
direction
fill_at / fill_price
normalized_sl / risk_distance
first_1r_at
current M30 trend
current M30 owner_id / owner start
current protected id / price
current external id / price
M30 protected->external range span
M30 range progress
remaining_to_external absolute distance
remaining_to_external / actual risk
latest M30 BOS/PB timestamps
current highest map identity
```

No later structure may be backfilled into this snapshot.

## 5. Post-+1R causal events to record

Between +1R and terminal +2R-or-SL, record only events as they become available.

### Same-direction M30 structure delivery

Record:

```text
INITIAL_BOS if applicable
continuation BOS
external price before event
external price after event
whether external moved outward in scenario direction
protected price before/after
owner_id before/after
event available_at
```

Primary derived fact:

```text
outward_external_refresh_after_1r = true/false
```

### M30 deterioration / opposite structure

Record:

```text
PROTECTED_BREAK
opposite directional structure event
owner change
trend transition / loss of scenario-direction authority
```

Keep exact causal timestamps and identities.

### Original +1R external interaction

Freeze the external that existed at T0.

Track:

```text
original_one_r_external_id
original_one_r_external_price
whether price delivered/reached it after T0
time of delivery
whether it was refreshed/replaced before +2R
```

Do not use a future external as if it existed at +1R.

## 6. Terminal snapshot

At exact first terminal event:

```text
+2R_REACHED
or
SL_AFTER_1R
```

record:

```text
resolved_at
exact exit-side price
time from +1R
MFE after +1R
MAE after +1R
current M30 trend
current owner_id
current protected id/price
current external id/price
current range progress if valid
same-direction BOS count since +1R
outward external refresh count since +1R
PB/opposite event count since +1R
owner-change count since +1R
whether original +1R external was delivered
```

This is observation only.

## 7. Pre-registered hypotheses

### H1 — Mature-state runner exception

For trades already near/through their current M30 external at +1R:

> +2R runners should more often receive a causal outward M30 structure refresh after +1R and before +2R than trades that exhaust.

If true, a mature state may still support continuation when structure renews.

### H2 — Room-rich failure exception

For trades with meaningful M30 protected-to-external range remaining at +1R:

> failures before +2R should more often show causal M30 deterioration — protected break, opposite event, owner loss/change, or failure to continue outward structure — before terminal SL.

### H3 — Descriptive-only falsification

If post-+1R refresh/deterioration does not consistently explain exceptions across markets/directions, then D-145 M30 maturity remains a descriptive association and must not be promoted into exit authority.

## 8. Analysis rules

Do not search for the pooled progress threshold that maximizes hit rate.

Primary analysis is relationship direction and mechanism frequency by:

```text
market
year
LONG/SHORT
M30 state availability
mature vs less-mature state described continuously / structurally
post-+1R refresh/deterioration event path
```

Where a binary structural distinction is used, it must have a direct market meaning, not a fitted numeric cutoff.

Example of structurally meaningful distinction:

```text
+2R price lies before the +1R-time current M30 external
vs
+2R price lies beyond that external
```

This is geometry, not a fitted percentile.

## 9. Runtime design

D-146 must be lighter than D-144.

Allowed tick-active research objects:

```text
actual trades that have already reached +1R and are unresolved to +2R/SL
```

Do not restore:

```text
Root mirror barriers
Sweep mirror barriers
CHoCH mirror barriers
FVG mirror barriers
flipped-direction stage populations
large target grids
```

Use the existing single unified CSV.

Implemented D-146 event rows:

```text
EDGE_AUDIT_D146_1R_STATE
EDGE_AUDIT_D146_M30_EVENT
EDGE_AUDIT_D146_ORIGINAL_EXTERNAL_DELIVERED
EDGE_AUDIT_D146_TERMINAL
EDGE_AUDIT_D146_CENSORED
```

The +1R-time M30 external is frozen as its own identity. A later M30 external is logged as a later causal state and is never backfilled into the +1R snapshot.

## 10. Strategy non-interference

D-146 may not:

```text
close a position
modify TP
modify SL
modify pending orders
authorize or reject Entry
modify map/structure/source/scenario state
change position size
```

Research functions may only read strategy state, maintain private audit state, and write `EDGE_AUDIT_*` rows.

## 11. Required validation

Before using D-146 evidence:

1. Check latest GitHub state and current code.
2. MetaEditor compile: 0 errors.
3. GOLD short-window Audit OFF vs ON.
4. Strip `EDGE_AUDIT_*`; all remaining rows must match exactly.
5. Validate each +1R primary tracker has a single terminal +2R/SL/censor state.
6. Validate M30 event timestamps are causal and no future external is backfilled.
7. Check runtime remains acceptable.

## 12. Development rerun order

After parity/integrity:

```text
GOLD 2025 first
then, as needed:
GOLD 2023
GOLD 2024
BTCUSD 2025
SILVER 2025
CADJPY 2025
```

This is still development/mechanism evidence.

`2021` remains untouched.

## 13. Promotion rule

D-146 itself has zero strategy authority.

Only if a post-+1R causal state transition survives markets and directions should the next phase design **one** controlled dynamic winner-extension variant.

A future variant must be compared against unchanged baseline and must evaluate:

```text
realized win rate
average winner R
cost-adjusted expectancy
drawdown
longest loss streak
annual/directional breadth
large-winner dependence
trade/exposure population changes
```

Do not mix that strategy variant with Entry-survival changes.

## 14. Separate unresolved problem

The current 2025 cross-market continuation Fill-to-1R rate is 41.1%.

D-146 does not solve it.

A separate later/parallel Entry-survival study must use only information known at or before Fill and must not import post-+1R maturity as an Entry filter.

## GOLD 2025 D-146 preliminary validation note — 2026-08-21

The uploaded GOLD 2025 unified ledger reproduced the prior continuation population exactly:

```text
EXTERNAL_CONTINUATION fills = 51
+1R before normalized SL = 30 / 51 = 58.82%
+2R before normalized SL = 20 / 51 = 39.22%
P(+2R | +1R) = 20 / 30 = 66.67%
D-146 armed = 30
D-146 terminal = 30
D-146 censored = 0
execution divergence = 0
```

The D-145 M30 maturity relation was reproduced on valid scenario-direction M30 ranges: +2R runners had lower median range progress (0.796 vs 0.918) and more remaining external room (0.954R vs 0.232R).

D-146 outward refresh was common in both constrained runners and constrained failures, so it is not by itself an exit discriminator. PROTECTED_BREAK appeared in 4/10 trade-level failures and 0/20 +2R winners, but the four trades correspond to only three independent M30 PB events and PB occurred after substantial giveback, so it is too late to claim winner-protection authority.

Instrumentation caveats discovered during analysis:

1. the PB callback is emitted before `EnterTransition`, therefore D-146 fields labeled post-state (`owner_changed`, `trend_lost`, `after_m30_*`) are pre-transition on PB rows;
2. the original D-146 summarizer used `external_available` rather than `one_r_m30_range_available` for one geometry classification, misclassifying three GOLD cases. Correct GOLD geometry is 11 room-rich / 13 external-constrained / 6 M30-range-unavailable.

These caveats do not invalidate exact +1R/+2R/SL barriers or PB timestamps, but D-146 MQL instrumentation is not silently repaired inside D-147. A separate instrumentation correction remains available if D-146 causal-state research is resumed.
