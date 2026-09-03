# V8 Slow-N Source-of-Move + Market-Universe Transfer Contract — 2026-09-03

Status: `FROZEN BEFORE NEW EXTERNAL RAW OUTCOMES`
Production authority: `NONE`
Reserve: `GOLD# 2021 UNTOUCHED`

## 1. Why this phase exists

Repeated causal GOLD-internal formulations failed to rank the economic direction of an already-formed ACCEPTANCE.
Further GOLD indicator mining is therefore closed.

This phase tests two distinct hypotheses and keeps them separate.

### S — Source-of-move hypothesis
External broker-market state may explain why the same GOLD ACCEPTANCE lifecycle is economically viable in one
environment and not another.

### U — Market-universe hypothesis
The structural/movement/runner lifecycle may be useful on some independent markets even when no single GOLD-only
direction gate is universal. Frequency should be gained by compatible markets, not by loosening a weak GOLD gate.

## 2. Outcome-blind universe freeze

The shortlist is fixed BEFORE new V8 P/L is opened:

```text
USDJPY#
XAUEUR#
BTCUSD#
```

All three are included. None may be removed because an older strategy performed badly there, and none may be
promoted because an older strategy performed well there.

Historical manifest evidence already establishes 2023-2025 source coverage and point metadata for all three.
Raw bytes still must pass the audit in this package before any new outcome calculation.

## 3. Required raw authority

Exact historical bytes expected:

| Symbol | File | SHA256 |
|---|---|---|
| BTCUSD# | BTCUSD#_M1_202301010000_202512310000.csv | d477f7063da7e91e959dc4126a4d49b7e8665316012428cb822ab6e97133c9fe |
| XAUEUR# | XAUEUR#_M1_202301030101_202512302358.csv | 906a46f0aaead4f8c97c3d569aa143424e3a4fe03431bdc015926092974fef95 |
| USDJPY# | USDJPY#_M1_202301020901_202512310000.csv | e86e92724330db492046331f593808f43cc99459a12c0b05a365f02f35450909 |

Do not substitute web data, another broker feed, or derived trade ledgers.

## 4. Pre-outcome data-quality screen

The supplied audit script must pass:
- exact SHA256;
- monotonic timestamps;
- zero duplicate timestamps;
- zero OHLC consistency violations;
- no negative spread;
- sufficient H4 ATR14 availability;
- report, but do not outcome-select on, spread/0.25S burden and gap statistics.

If one market fails raw integrity, mark it `DATA_UNAVAILABLE/EXECUTION_ENVIRONMENT_MISMATCH`; do not call it a
strategy failure.

## 5. Branch U — frozen per-market Slow-N transfer

Each market is treated independently.

### Scale
`S = previous existing completed H4 Wilder ATR14`.

### ONSET model
Use the current Slow-N 86-feature, 4-class family without market-specific indicator invention:

```text
class 0 = either-side 0.25S reached by 15m
class 1 = first reached 15-30m
class 2 = first reached 30-60m
class 3 = not reached by 60m
P15 = class-0 probability
```

Use the same deterministic Phase-0 / Phase-2 25-minute outcome-blind training sampling semantics.

Chronology:
- train 2023 -> evaluate 2024;
- after all architecture is frozen, train 2023-2024 -> evaluate 2025.

No 2025 threshold rescue after seeing 2024.

### fresh75
Same semantic crossing:
`prior completed-M5 P15 < .75 and current P15 >= .75`.

Do not replace `.75` per market.

### ACCEPTANCE
Exactly the current lifecycle:
1. origin = last completed M1 close at the decision;
2. first directional M1 close within 15m that reaches +/-0.25S = reveal;
3. actual reveal leg fixed from origin to reveal close;
4. >=25% pullback of that actual leg;
5. origin remains wick-intact through the pullback;
6. M1 close reclaims the original fixed +/-0.25S reveal threshold;
7. pullback extreme begins AFTER the reveal bar;
8. no hindsight abstention.

No symbol-specific pullback fraction.

### Economic controls
Report at minimum, unchanged across symbols:

A. routine base:
- executable next-M1-open entry after acceptance;
- TP +0.25S;
- SL -0.25S;
- stop-first same-bar ambiguity;
- 240m maximum lifecycle.

B. frequent base + runner:
- 50% at +0.25S;
- residual target +0.75S;
- initial SL -0.25S;
- after partial, runner stop = entry/B.E.;
- 240m maximum lifecycle.

C. runner characterization:
- 10m and 15m close-intact state;
- realized MFE/S;
- 2024 distributional quantiles may characterize 2025, but no P/L-selected quantile threshold.

All spread/cost calculations must use each symbol's own point/execution metadata. Cross-market raw SPREAD integers
must never be compared as if they had common economic units.

## 6. Branch U — reporting and promotion

Report EVERY market, phase, year, direction:
- fresh75 N and movement hit rate;
- acceptance N / fresh;
- base WR and cost-adjusted E[R];
- avg winner and payoff ratio;
- base+runner WR/E[R]/avg winner;
- DD proxy and loss streak;
- MFE15 -> future large-continuation AUC;
- week-block bootstrap;
- overlap-collapsed control;
- cost sensitivity.

No market may disappear from the table after its outcome is known.

The research claim is allowed to be:
- `portable across all`;
- `market-specific suitability`;
- `fails transfer`.

Market-specific suitability is acceptable if the shortlist was frozen before outcome and evidence is broad enough.
Do not invent symbol-specific thresholds after the outcome.

## 7. Branch S — GOLD source-of-move test

Population:
current exact Slow-N GOLD P0/P2 ACCEPTANCE only.

Decision timestamp for external information:
the acceptance event completion. Only external rows strictly earlier than the executable next-M1 entry are allowed.

Primary outcome:
`+0.25S base target before -0.25S base stop` from the executable entry.
Right-censored events are not converted to wins/losses.

### External primary information
USDJPY# and XAUEUR#.

For each horizon:
`5 / 15 / 30 / 60 / 120 / 240m`

Use only causal:
- signed displacement normalized by own-market prior H4 ATR14;
- close location in the observed rolling range;
- path efficiency;
- signed body bias;
- realized range / own-market scale;
- observation age / gap flag.

Cross-relations:
- GOLD direction-oriented agreement with XAUEUR movement;
- GOLD direction-oriented co-movement with USDJPY;
- short-vs-long horizon changes in those relations.

No hand-coded `USDJPY up => GOLD down` threshold.

BTCUSD# is a negative-control source, not a primary economic explanation.

### Models
Low-dimensional regularized logistic first.
No HGB/NN rescue unless the fixed linear test first shows stable incremental information.

Comparisons:
- C0: intercept + frozen GOLD causal acceptance geometry only;
- C1: C0 + USDJPY + XAUEUR source-of-move features;
- C2: C1 + BTC negative-control features.

Chronology:
- fit only 2024 GOLD acceptance -> evaluate 2025;
- 2026 is optional frozen stress only if a comparable external panel is available.

### Promotion gate
Continue only if:
1. source age/data-quality rules pass;
2. C1 improves proper scoring over C0 in BOTH P0 and P2 for 2025;
3. direction ranking does not reverse materially between P0/P2;
4. week-block uncertainty is not entirely driven by a few weeks;
5. C2 does not show that BTC generic features carry the result while USDJPY/XAUEUR do not;
6. no threshold rescue is needed.

If 2025 fails, close S. Do not tune horizons/thresholds to rescue it.

## 8. Separation rule

A market may be suitable for the V8 lifecycle even if it is not useful as an external source for GOLD.
Likewise an external symbol may contain useful source-of-move information without itself being a good V8 trading market.

Do not merge Branch S and Branch U conclusions.

## 9. Reserve

GOLD# 2021 remains untouched through this entire phase.
