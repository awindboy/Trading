# V8-000 — Causal Chart Representation Research Contract

Status: `PRE-REGISTERED DEVELOPMENT CONTRACT`
Date: `2026-08-30`
Production authority: `NONE`
EA authority: `NONE`

## 1. Research question

Primary claim:

> GOLD contains economically useful, future-hidden contextual information that is better preserved by a
> learned multi-timeframe chart representation than by prematurely reducing the chart to a small collection
> of human-defined market-state labels and scalar thresholds.

Secondary claim:

> When anchored at objectively observable events, the learned context can improve action-conditioned decisions
> such as enter, wait, hold, add, reduce and exit under sequential campaign accounting.

These claims must be tested separately.

## 2. What V8 does not assume

V8 does not assume that any of the following has a unique correct threshold definition:

```text
trend
range
breakout
turning point
healthy pullback
mature move
climax
```

These descriptions may emerge in human interpretation of examples but are not required ground truth.

## 3. Representation hypothesis

A candlestick chart is mathematically derived from OHLC data, but representation matters.

Scalar summaries can destroy spatial and temporal relationships even when no raw information is technically
lost at the source.

V8 therefore compares representations rather than assuming that manually engineered scalars are sufficient.

Required comparison:

```text
R0 — hand-engineered scalar baseline
R1 — raw numerical multi-timeframe sequence
R2 — rendered visual multi-timeframe chart
R3 — fused visual + numerical representation
```

The claim is not that images contain magical extra market information. The claim is that chart-preserving
inductive bias may allow a model to learn conditional relationships that are difficult to specify faithfully
as handcrafted rules.

## 4. Information boundary

At any decision timestamp `t`:

- only completed/available market information at or before `t` may be used;
- chart images may show no bar or annotation that becomes known after `t`;
- confirmed structures appear only after their confirmation delay;
- input scaling uses the visible historical window only or a causally fitted transform;
- labels/outcomes begin strictly after the decision information boundary;
- current position state includes only actions actually taken before `t`.

No rendering exception is allowed.

## 5. Observable anchor population

The first anchor population is intentionally broader than rare H1 Double-B alone.

Candidate anchors are factual, causally detectable events:

- Double-B confirmation;
- moving-average interaction;
- Bollinger interaction;
- prior-session high/low interaction;
- session-open structural interaction;
- causally confirmed S/R interaction;
- displacement/activity shock;
- campaign management milestone.

Anchor definitions must be frozen before their outcome distributions are compared.

Do not choose anchors because their P/L looked attractive in the same data.

## 6. First-stage learning targets

V8-001/002 should not jump directly to a complex RL policy.

First establish whether the representation contains stable future-path information.

Possible future-hidden targets include:

- normalized MAE/MFE over fixed horizons;
- future path quantiles;
- time to upward/downward excursion levels;
- probability of revisiting visible levels;
- probability of reaching causal risk multiples under a frozen reference risk geometry.

These are diagnostic targets, not final strategy authority.

## 7. Action-conditioned stage

Only after representation skill survives future-hidden diagnostics may V8 evaluate actions.

The action-conditioned stage asks:

```text
Given the current context and current position,
what is the future distribution if exposure is kept, opened, increased, reduced or closed?
```

Historical market paths are assumed exogenous at the intended account scale, but transaction costs and
exposure changes must be applied explicitly.

## 8. Sequential campaign accounting

A decision sequence is a campaign, not a bag of independent events.

Rules:

- one underlying campaign ID;
- no independent-trade credit for overlapping signals during an existing campaign;
- every add increases recorded risk/exposure;
- every reduction realizes part of campaign P/L;
- runner P/L remains attached to the same campaign;
- daily and campaign metrics are both reported.

## 9. Development data

For V8:

```text
GOLD# 2022-2026 = OPEN / CONSUMED DEVELOPMENT EVIDENCE
```

Use chronological splits only as development diagnostics.

Do not describe 2025 or 2026 as pristine simply because a particular V8 model has not trained on them before;
the project has already inspected these periods.

## 10. Final reserve

Repository authority currently records:

```text
GOLD# 2021 = UNTOUCHED
```

The reserve remains unopened until:

- renderer is frozen;
- input windows are frozen;
- event population is frozen;
- representation family/model-selection rule is frozen;
- campaign action set is frozen;
- risk/cost accounting is frozen;
- success/failure metrics are frozen.

## 11. Required baselines

At minimum compare against:

- same-anchor unconditional action statistics;
- hand-engineered scalar model;
- numerical-sequence-only model;
- simple momentum/mean-reversion controls;
- visual-only model;
- fused model.

A large neural model receives no credit merely for fitting training data better.

## 12. Metrics before strategy promotion

Representation diagnostics:

- future-hidden predictive skill;
- calibration where applicable;
- stability by year/session;
- nearest-neighbor/retrieval coherence;
- ablation of visual vs numeric channels.

Economic diagnostics:

- campaigns;
- actions per active day;
- entries/adds/reductions/exits;
- realized campaign win rate;
- average positive/negative campaign;
- net expectancy per initial risk unit;
- total R;
- maximum drawdown;
- maximum loss streak;
- maximum simultaneous risk;
- exposure time;
- spread/cost contribution;
- MAE/MFE;
- dependence on a small number of runners.

## 13. Success is not a pretty backtest

V8 is not promoted because a large model can produce a visually convincing equity curve.

A claim must survive:

- causal input audit;
- representation baselines;
- chronological future-hidden development diagnostics;
- sequential campaign replay;
- full-cost accounting;
- frozen untouched validation.

## 14. No-production boundary

No V8 development result changes an MT5 production Entry, SL, TP, sizing or execution path.

An EA may be built later only as a research/validation implementation after V8 freezes a sufficiently
specified policy.
