# V8 Research Instructions

Status: `ACTIVE`
Generation: `V8`
Active branch: `Movement Probability / Human Decision Support`
Production authority: `NONE`
EA authority: `NONE`
Direction authority: `NONE`
Market: `GOLD#`
Untouched reserve: `GOLD# 2021`

## 1. Current V8 thesis

V8 began as a representation-first attempt to avoid forcing ambiguous chart concepts into arbitrary deterministic labels.

That principle remains valid, but the research has now produced a more specific empirical result:

> GOLD historical context contains strong information about near-term movement intensity / barrier crossing, while stable direction information has not been demonstrated.

The active V8 branch therefore focuses on **movement probability as human decision support**, not autonomous direction.

## 2. Do not conflate three different questions

Keep these separate:

```text
A. Is a meaningful move likely soon?
B. Which direction will it move?
C. Will a particular trade be profitable?
```

Current authority:

- A: positive open-development evidence;
- B: no authority;
- C: no authority.

A high movement probability must never be silently converted into LONG/SHORT or automatic entry permission.

## 3. Active movement target

The current human-facing target is:

```text
C0 = completed M5 decision close
barrier = +/- 10.0 GOLD price units
H in {15m, 30m, 60m}

P(price reaches C0 + 10.0 or C0 - 10.0 within H)
```

The target is direction-free.

Changing the `10.0` barrier requires retraining and renewed validation. Do not expose a runtime barrier input that reuses frozen model coefficients.

## 4. Active representation

The active movement model does not require visual/raster input.

Use explicit causal numerical range/volatility/activity features. Current portable MT5 representation uses 53 features derived from M1 history over multiple windows including approximately:

```text
5 / 15 / 30 / 60 / 120 / 240 / 480 / 1440 M1 rows
```

Feature families include:

- realized squared price changes;
- high-low range accumulation;
- rolling max(high)-min(low);
- absolute close-change accumulation;
- candle body activity;
- current range/true-range/absolute-change state;
- short-vs-long activity ratios;
- time context where frozen in the model.

Broad RSI/MACD/EMA accumulation is not the active path unless a controlled incremental-value test proves added movement information.

## 5. Historical indicator/price representation lessons

Earlier V8 research established useful general rules:

- price-level variables may be represented relative to a common event close `C0` when the task requires chart-geometry invariance;
- indicator histories can be useful representations, but adding more indicators does not create information that is absent from the underlying market path;
- level + change/dynamics channels can be more useful than level alone;
- preprocessing must be evaluated chronologically and causally rather than assumed from generic ML literature.

Do not revive a failed normalization or architecture simply because it is fashionable in time-series research.

## 6. Factual event anchors

Current main-chart shadow markers:

- H1 Double-B confirmation;
- M5 SMA20 contact episode start;
- M5 BB20 upper contact episode start;
- M5 BB20 lower contact episode start.

These events are attention anchors only.

They do not encode:

```text
TREND
RANGE
BREAKOUT
TURNING
LONG
SHORT
```

Event identity by itself was much weaker for movement probability than recent range/volatility state.

## 7. Causality rules

Every model input and historical display is part of the information boundary.

Required:

- use completed bars only for displayed probabilities;
- no future-confirmed event may be marked early;
- no future price may enter scaling or feature construction;
- training examples must be purged if their label-resolution interval crosses a validation/evaluation boundary;
- train/validation preprocessing must fit on past data only;
- historical chart display must use the model that would have existed before that historical evaluation period.

Current walk-forward display policy:

```text
2024 <- train 2022-2023
2025 <- train 2022-2024
2026 <- train 2022-2025
```

No current authority exists for pre-2024 display or post-2026 extrapolation.

## 8. Direction research status

Do not resume incremental direction feature mining as the default task.

Direction research has already tested, among other things:

- OHLC-only and indicator-history sequences;
- event-centered chart geometry;
- visual and fused representations;
- multi-lag dynamics;
- robust normalization;
- fractional differentiation;
- self-supervised masked reconstruction;
- linear / LightGBM / TCN / patch-Transformer models;
- competing-risk direction+time heads;
- nearest-neighbor retrieval;
- event-family splits;
- Double-B follow-up chains;
- overlap weighting and one-active populations;
- rolling / online retraining;
- simple meta-labeling.

Stable strong direction information did not survive later development periods.

A new direction branch requires a materially new source of information or a new preregistered causal hypothesis.

## 9. Movement-probability evidence

The portable continuous-M5 logistic model remains strongly discriminative when evaluated only at factual event timestamps.

Open-development event-subset AUC:

```text
15m: 2024 0.865 / 2025 0.873 / 2026 0.815
30m: 2024 0.844 / 2025 0.851 / 2026 0.796
60m: 2024 0.807 / 2025 0.829 / 2026 0.781
```

These are not untouched validation results.

## 10. Active implementation

Artifact:

`mt5/indicators/V8MovementProbabilityIndicator.mq5`

Purpose:

- separate subwindow with continuous 15m/30m/60m movement-probability lines;
- factual event triangles on the main chart;
- configurable event-family colors;
- marker tooltip with probabilities at the event decision time;
- no trade/order action;
- no direction output.

The current forming M5 candle must remain blank.

## 11. Runtime validation before discretionary reliance

Before using the indicator as a serious human filter:

1. compile in the user's actual MetaEditor;
2. verify broker M1/M5/H1 history availability;
3. verify event timing visually;
4. compare selected timestamps against the Python parity reference where feeds match;
5. confirm no trade/order side effects;
6. begin prospective logging of every eligible event, including ignored events.

## 12. Prospective human+AI study

The next practical question is not whether the movement score predicts direction.

It is:

> Does the trader's discretionary directional/trade performance improve as movement probability increases?

Log before outcome:

- event;
- 15m/30m/60m probabilities;
- human LONG/SHORT/WAIT/SKIP;
- actual trade parameters if any;
- realized outcome.

Do not tune a threshold from remembered winners or selected screenshots.

## 13. Campaign and final-strategy discipline

The original final strategy requirements remain unchanged:

- realized win rate at least 50%;
- average winner meaningfully above 1R;
- positive full-cost expectancy;
- acceptable drawdown / loss streak / exposure;
- no duplicate same-move trade credit;
- preferably multiple legitimate opportunities when supported by the market.

Movement probability is currently a decision-support input, not evidence that these strategy requirements are met.

## 14. Data roles

GOLD# 2022-2026 is open/consumed development evidence.

`GOLD# 2021` remains untouched and locked.

Do not open 2021 until a claim-grade candidate, preprocessing/model contract and evaluation protocol are frozen.

## 15. Required reading order

On every resumed V8 session:

1. refresh GitHub HEAD;
2. `docs/ea/v8/AGENTS_V8.md`;
3. `docs/ea/v8/HANDOFF_V8.md`;
4. `docs/ea/v8/V8_RESEARCH_JOURNEY.md`;
5. `docs/ea/v8/V8_005_MOVEMENT_PROBABILITY_INDICATOR.md`;
6. `docs/ea/v8/DECISIONS_V8.md`;
7. `docs/ea/v8/RESEARCH_STATE_V8.md`;
8. current indicator source.


## V8-A / V8-B branch contract — 2026-08-31 addendum

V8 now contains two explicitly separated probabilistic branches.

### V8-A — frozen movement marginal

`p_H = P(any +/-10.0 move within H)` for H=15m/30m/60m.

Do not alter V8-A from V8-B research.

### V8-B — conditional side

`q_H = P(UP first | a move occurs within H, causal context)`.

Joint probabilities are `p_H*q_H`, `p_H*(1-q_H)`, and `1-p_H`.

Current V8-B evidence supports M5 MA20/upper-BB/lower-BB event anchors only. H1 Double-B has no direction authority.

Movement probability is not a default side feature: controlled tests found that direct V8-A probability inputs and gating interactions did not improve conditional side prediction.

V8-B must always be evaluated both conditionally and on the full event population, and must pass non-overlap checks before promotion.
