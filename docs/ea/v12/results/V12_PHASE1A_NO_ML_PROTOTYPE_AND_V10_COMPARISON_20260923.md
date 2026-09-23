# V12 Phase-1A no-ML prototype and V10 comparison

Date: `2026-09-23`

Status: `FIRST V12 PROTOTYPE COMPLETE / V10 REPLACEMENT GATE FAILED / NO TRADE AUTHORITY`

## Question and frozen scope

Phase 1A tested whether a mechanical CRT rejection Child can improve the stop
population before HA, Wave, or ML is added. It retained only completed
`HIGH_SWEEP_RETURN -> SHORT` and `LOW_SWEEP_RETURN -> LONG` parents and compared:

1. C3-open control with a C2-extreme Hard SL;
2. relative-thick Model #1 confirmation with a C2-extreme Hard SL; and
3. the same confirmation with a trigger-candle structural Hard SL.

The primary destination is C1 midpoint. The opposite C1 edge is a diagnostic
surface. Outside-acceptance, true MSS, retries, costs, sizing, and discretionary
chart labels are not implemented.

## Pipeline and causal audit

- Input: the frozen `1,459`-parent Phase-0 pack plus chronological raw M1.
- Contract: `v12-phase1a-model1-v2`; no fitted body threshold, minimum-R rule,
  session veto, or no-chase rule.
- Decisions and outcomes are separate files. Entry, pre-entry stop/target guards,
  SL, target, expiry, and same-M1 ambiguity are processed chronologically.
- The builder parsed `0` post-cutoff price rows.
- `1,217` family/risk decision records produced `426` filled variant records.
- Both the primary and independent rebuild passed complete-pack validation. All
  ten generated files, including the manifest and chart, are byte-identical.

Two audit corrections preceded the retained result. The unretained v1 guarded
C1 midpoint too late and was replaced by v2 before v2 outcomes were generated.
An implementation audit then found that a clock-equality lookup omitted 80
Friday-to-Monday D1 C3 bars. The already-frozen contract required the next
completed parent bar, so the sequence lookup was corrected, regression-tested,
and both final packs were rebuilt. Neither discarded output is evidence.

## Parent and execution accounting

Parent dispositions sum to the full `1,459` records:

| Disposition | Records |
|---|---:|
| Model #1 selected | 383 |
| Outside-acceptance branch not implemented | 653 |
| Dual branch not directionally authorized | 155 |
| No extreme interaction | 199 |
| No sweep-direction body candle | 38 |
| No confirmation before C3 close | 30 |
| Completed C3 unavailable | 1 |

Across all three variants, no execution was recorded for `533` pre-entry
midpoint consumptions, `247` pre-entry stop invalidations, `5` targets already
consumed at entry, `3` stops already invalid at entry, and `3` same-M1
sweep/midpoint ambiguities. These are not backfilled as losses or trades.

## Full consumed-history T1 result

Drawdown is realized structural R aggregated by terminal timestamp. It is not
V10's authoritative overlapping-exposure portfolio drawdown.

| Family / Hard SL | Decisions | Fills | Stop rate | Net R | PF | R / 100 fills | DD R | Max stop streak |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| C3 open / C2 extreme | 451 | 213 | 41.78% | -1.12 | 0.99 | -0.53 | 20.75 | 5 |
| Model #1 / C2 extreme | 383 | 156 | 31.41% | +11.68 | 1.21 | +7.49 | 14.25 | 3 |
| Model #1 / trigger structure | 383 | 57 | 38.60% | +2.89 | 1.13 | +5.07 | 8.95 | 5 |

The trigger-stop variant is not stable by year: `-5.44R` in 2022, `-1.57R` in
2023, `+0.19R` in 2024, `+1.32R` in 2025, and `+8.39R` in 2026, on only 8–14
fills per year.

## Matched V10 comparison

The fixed comparison window is `2024-10-01 01:00` through
`2026-08-28 23:57`, the actual selected-R7G interval. Values are spreadless
structural R so this is a strategy-mechanism comparison, not MT5 economics.

| Strategy | Decisions / children | Funded units | Stopped units / 100 | Net R | PF | R / 100 units | DD R | Max streak | >=2R / >=5R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| V10 selected, one unit | 1,649 | 1,649 | 14.07 | +284.37 | 1.58 | +17.24 | 24.20 | 5 | 121 / 16 |
| V10 R7G actual units | 1,649 | 3,881 | 12.52 | +741.01 | 1.68 | +19.09 | 57.00 | 5 | 273 / 101 |
| V12 C3 open / C2 SL | 183 | 80 | 47.50 | -9.74 | 0.76 | -12.18 | 15.33 | 5 | 3 / 0 |
| V12 Model #1 / C2 SL | 159 | 62 | 40.32 | -5.59 | 0.80 | -9.02 | 11.29 | 3 | 3 / 0 |
| V12 Model #1 / trigger SL | 159 | 26 | 26.92 | +8.84 | 2.26 | +34.00 | 2.68 | 2 | 3 / 0 |

The recent trigger-SL row is attractive only in isolation. It has 26 fills,
`84%` no execution, no >=5R outcome, and a higher stopped-unit burden than both
V10 comparators. Its full-history PF is only `1.13`, with losses concentrated in
2022–2023. It therefore does not establish a scalable V10 replacement.

## Mechanism audit

| Scope / change | Baseline fills blocked | What the blocked fills carried | Common-fill entry/SL delta |
|---|---:|---:|---:|
| Full: add confirmation | 18 | 13 stops, 5 targets, -7.85R | -17.21R |
| Matched: add confirmation | 9 | 6 stops, 3 targets, -1.36R | -3.69R |
| Full: C2 SL -> trigger SL guard | 99 | 28 stops, 50 targets, 21 expiries, +3.98R | -4.81R |
| Matched: C2 SL -> trigger SL guard | 36 | 18 stops, 12 targets, 6 expiries, -13.92R | +0.51R |

Confirmation really did avoid some stops, but delayed entry cost more R among
the fills that remained. The trigger-stop guard looked selective only in the
recent matched window; over the full history it removed net-positive baseline
capital and worsened common-fill R. This is era instability, not a validated
stop-recognition mechanism.

## Decision

Phase 1A completes the first causal, reproducible V12 prototype and gives V10 a
fair matched comparator. It fails the replacement gate. The branch is retained
as a no-ML baseline and mechanism diagnostic, not tuned into a rule and not
granted sizing, EA, trade, or production authority.

Any next V12 branch must be predeclared rather than threshold-mined from these
outcomes: a causal true-MSS definition, a separately contracted outside-
acceptance continuation branch, or matched HA/Wave sensor ablation on the frozen
ledger. The post-cutoff chronology remains unread and GOLD# 2021 remains sealed.
