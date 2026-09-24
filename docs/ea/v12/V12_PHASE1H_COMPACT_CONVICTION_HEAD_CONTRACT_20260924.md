# V12 Phase-1H compact conviction-head contract

Date frozen: `2026-09-24`

Status: `CONSUMED-DEVELOPMENT REASSEMBLY / NO TRADE OR SIZING AUTHORITY`

Contract: `v12-phase1h-compact-conviction-head-v1`

## Decision being tested

Phase 1G showed that continuous intraday path contains stop-risk information,
but its full head used 119 numeric fields and did not consistently improve the
right-tail outcome. Phase 1H asks whether the result survives a deliberately
small representation and whether HA or Wave adds incremental information after
that path is known.

This is not independent validation. The mechanism was discovered on the same
consumed chronology. Phase 1H may reject, simplify, or freeze a future test; it
cannot confirm edge.

## Frozen primary representation

The primary compact head uses the existing V10/CRT structure fields, ten
continuous cyclical clock coordinates, and exactly eight direction-symmetric
path fields for each of four causally completed source boxes:

- favorable and opposed boundary-breach state;
- favorable-minus-opposed normalized extension;
- direction-aligned M1-close dwell;
- outside-to-inside reentries per observed hour;
- log minutes since the last boundary transition;
- direction-aligned current settlement;
- direction-aligned post-box path efficiency.

No raw absolute price, named session bucket, event-family label, cross-box
inventory, target-distance threshold, or outcome-selected field enters the
primary head. The primary source-field count may not exceed 50.

## HA and Wave ablations

HA and Wave cannot create a candidate or veto one. They are additive ablations:

- completed-H4 FAST/STD/SLOW body margins normalized by prior H4 ATR180;
- alignment and disagreement counts against the Child direction;
- the eight completed pre-decision Wave coordinates retained from V11.

No forming-H4 `+60m` feature is allowed because this head is evaluated at the
original Child decision timestamp.

## Competing outcomes and causal bands

Each feature set fits separate weighted ridge-logistic heads for:

- `P(Hard SL)`;
- `P(>=5R right-tail presence)`.

The frozen conviction coordinate is:

```text
P(>=5R) - P(Hard SL)
```

Unlike the Phase-1G descriptive test-fold quintiles, Phase 1H obtains quintile
cut points from that fold's training predictions only and applies them unchanged
to the later test period. Test outcomes and the future test score distribution
cannot define a band.

The only capital probe is a non-veto shadow tilt: multiply existing V10 units by
`0.75 / 1 / 1 / 1 / 1.25` for Q1 through Q5. Report raw exposure and per-unit
economics; never call lower exposure an improvement without identifying stopped
and right-tail units moved.

## Frozen gates

The compact head must jointly pass:

- both-head log-loss improvement versus continuous clock;
- lower Q5 stopped-unit rate in every fold;
- positive and at-least-population Q5 R/unit in every fold;
- at least 10% funded-unit Q5 coverage in every fold;
- lower shadow-tilt stopped units per 100 in every fold;
- pooled and fold-level R/unit and right-tail retention gates;
- LONG/SHORT and train-defined liquidity-era stability.

HA or Wave survives only if it improves mean log loss for both heads, never
worsens a fold by more than `0.02`, and passes every capital gate. A good stop
score that moves the right tail into low conviction is failure.

## Authority boundary

All source chronology through `2026-09-18 23:57` is already consumed. GOLD#
2021 and post-cutoff chronology remain sealed. This phase grants no admission,
veto, retry, exit, capital, EA, or production authority.
