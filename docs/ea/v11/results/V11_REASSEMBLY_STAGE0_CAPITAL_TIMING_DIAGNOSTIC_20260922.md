# V11 reassembly stage-0 capital-timing diagnostic

Date: `2026-09-22`

Status: `CONSUMED DEVELOPMENT EVIDENCE / NO FIXED WAIT, MODEL, SIZING, OR PRODUCTION AUTHORITY`

## Question

Does V10 hide a useful strategy dimension by funding every selected Child at the same instant that the candidate is recognized? The audit evaluates fixed delayed-entry probes using trade coverage, stop burden, win rate, structural R, R7G-weighted R, stop streak, drawdown, and descriptive equal-drawdown capacity together.

## Population and parity

- MT5 embedded-model event rows: `4,050`;
- causal FAST-k1 transition episodes: `2,101`;
- matched 2024-2026 k1 rows: `1,197`;
- non-warmup R7G-intended selected k1 rows: `626`;
- selected-audit parity: `626/626`.

Known market-closed `ORDER_FAIL` events remain intended strategy Children, consistent with the existing V10 execution-study boundary. The audit is not a broker-fill reconstruction.

## Overall frontier

| Policy probe | Trades | Hard SL | Stop rate | Win rate | Structural R | R7G-weighted R | Max stop streak |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| immediate | 626 | 133 | 21.25% | 35.78% | +117.31R | +279.65R | 3 |
| +60m all survivors | 534 | 101 | 18.91% | 35.58% | +97.20R | +230.67R | 3 |
| +120m all survivors | 575 | 86 | 14.96% | 35.83% | +89.37R | +203.58R | 3 |
| +180m all survivors | 544 | 65 | 11.95% | 39.34% | +122.00R | +259.82R | 2 |

The +60m and +120m probes reduced stops but failed economically. The +180m probe retained `86.9%` of trades and `92.9%` of weighted R while removing `51.1%` of Hard SLs. This changes the research priority but does not authorize a fixed wait.

## Stability

The +180m stop rate was lower in each observed year:

| Year | Immediate stops/rate | +180m stops/rate | Immediate weighted R | +180m weighted R |
| --- | ---: | ---: | ---: | ---: |
| 2024 | 21 / 22.11% | 11 / 13.58% | +22.55R | +49.84R |
| 2025 | 63 / 19.94% | 27 / 9.93% | +173.78R | +135.92R |
| 2026 partial | 49 / 22.79% | 27 / 14.14% | +83.32R | +74.06R |

Direction asymmetry is material:

| Side | Immediate trades/stops | +180m trades/stops | Immediate weighted R | +180m weighted R |
| --- | ---: | ---: | ---: | ---: |
| LONG | 410 / 99 | 351 / 47 | +267.50R | +266.31R |
| SHORT | 216 / 34 | 193 / 18 | +12.15R | -6.49R |

The result cannot justify a post-hoc LONG-only or no-SHORT rule.

## Capacity illustration

At 1% risk per R7G unit, immediate funding ended at `10.47x` with `26.74%` maximum drawdown. The +180m probe ended at `9.94x` with `21.84%` drawdown. Matching the immediate drawdown by bisection raised the probe to `1.234%` risk per unit and `15.80x` ending equity.

This calculation is sequential, no-cost, consumed-data compounding. It ignores spread, slippage, broker lifecycle, and portfolio overlap. It demonstrates why raw R alone is an incomplete objective; it does not establish deployable leverage.

## Existing ML synergy check

The two R5 outputs were kept separate:

```text
Spearman(P_STOP, wait180_delta_weighted_R)       0.010
Spearman(mu_nonstop, wait180_delta_weighted_R)   0.022
```

Median `P_STOP x mu_nonstop` quadrant effects changed sign across 2024, 2025, and partial 2026. Existing R5 outputs therefore do not supply a stable selective timing rule. A new action-value target is required if ML is revisited.

## Decision

- Retain capital timing as a separate V11 research dimension.
- Reject promotion of any fixed 60/120/180-minute wait.
- Do not scalarize the evaluation back to raw R or STOP count alone.
- The next model question, if pursued, is `value(fund now) - value(continue observing)`, evaluated chronologically and at complete-policy level.
- Keep FAST candidate creation, Hard-SL causality, and campaign exit separate from funding and opposite-direction authorization.

## Reproduction

- script: `research/v11/analyze_v11_reassembly_stage0.py`;
- ignored output: `output/v11_reassembly_stage0_20260922/`;
- manifest: `V11_REASSEMBLY_STAGE0_MANIFEST.json` in that directory.
