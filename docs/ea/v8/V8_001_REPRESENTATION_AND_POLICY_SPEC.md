# V8-001 — Representation and Policy Specification

Status: `INITIAL SPEC / PRE-IMPLEMENTATION`
Date: `2026-08-30`

## 1. Design objective

Build a machine-readable equivalent of what a trader actually sees without pretending that ambiguous market
meaning has already been solved.

The system must preserve:

1. chart geometry;
2. exact numerical state;
3. observable events;
4. current campaign state.

It must not require a prior hard answer to:

```text
Is this a trend?
Is this a range?
Is this a breakout?
Is this a turning point?
```

## 2. Multi-timeframe visual observation

Initial four-panel observation:

```text
H1 — broad structural/session context
M15 — intermediate geometry
M5 — local setup development
M1 — execution path
```

Each panel should use a fixed pixel size and a frozen number of completed bars after the representation audit.

The first implementation should support the same overlays a human would reasonably inspect:

- candles;
- Bollinger A and B where defined;
- selected moving averages;
- causal session boundaries;
- event markers;
- causal S/R lines.

Overlays must be individually ablatable.

## 3. Numerical observation

Alongside the image, retain exact arrays for:

- OHLC;
- spread;
- tick volume/activity proxy;
- MA/Bollinger values;
- normalized volatility;
- timestamp/session coordinates;
- objective level distances;
- event flags;
- position/campaign facts.

The numerical branch prevents image rasterization from becoming execution authority.

## 4. Visual scaling

Rendering must not leak future scale.

Allowed approaches:

- visible-window min/max with fixed padding;
- causal volatility-normalized coordinates;
- a frozen deterministic transformation fitted only on training history.

Not allowed:

- full-day high/low when future bars are not yet known;
- full-event outcome range;
- global year min/max computed using future data at decision time if the value becomes an input shortcut.

## 5. Event tokens

Event tokens tell the model **what objectively happened**, not what it means.

Example token fields:

```text
event_type
event_side
event_time
event_level
distance_from_MA
distance_from_band
distance_from_session_high_low
spread
activity
current_campaign_state
```

For a Double-B event the token may say `UPPER_DOUBLE_B_CONFIRMED`.

It must not say `BREAKOUT_DOUBLE_B` unless that label is being used only in a separate human-audit table.

## 6. Encoder architecture candidates

The first tournament should compare small models before scaling.

Visual candidates:

- compact CNN;
- small Vision Transformer or patch encoder.

Numerical candidates:

- 1D temporal convolution;
- compact Transformer/patch encoder.

Fusion:

```text
z_visual
+ z_numeric
+ event token
+ position token
→ fused latent z_t
```

Do not add model size merely because training metrics improve.

## 7. Self-supervised option

A self-supervised stage is permitted because unlabeled causal chart sequences are abundant.

Potential objectives:

- masked-patch reconstruction;
- temporal contrastive learning;
- next-window representation prediction;
- cross-timeframe consistency.

Self-supervised pretraining must respect chronological train/validation boundaries.

## 8. Retrieval audit

Before trusting a latent representation, retrieve nearest historical contexts for a set of frozen query
timestamps.

Human audit questions:

- do neighbors share meaningful chart geometry without being exact duplicates?
- do they come from multiple years?
- are they merely matching time-of-day or volatility scale?
- do future paths become more coherent than unconditional anchors?
- does visual fusion add information beyond numerical-only neighbors?

Retrieval is diagnostic, not a discretionary label source.

## 9. Reference future-path targets

The initial representation stage may use frozen diagnostic horizons.

Targets should describe path, not only terminal return.

Example vector:

```text
MFE_15m
MAE_15m
MFE_60m
MAE_60m
MFE_240m
MAE_240m
terminal_return_15m
terminal_return_60m
terminal_return_240m
```

Scale by a causally known volatility/risk unit.

Exact horizon/normalization constants must be frozen before model comparison.

## 10. Reference action evaluation

A later action model may use the same historical path to evaluate simple counterfactual exposure changes.

Flat:

- WAIT;
- ENTER_LONG;
- ENTER_SHORT.

Long:

- HOLD;
- ADD one frozen risk fraction;
- REDUCE one frozen fraction;
- EXIT.

Short symmetric.

Do not optimize dozens of add/reduce percentages in the first controller.

## 11. Risk geometry boundary

V8-001 is primarily a representation study.

The first economic controller should use one frozen reference risk geometry so that representation comparison
is not contaminated by simultaneous SL/TP optimization.

Structural risk architecture can be researched only after the representation demonstrates stable information
value.

## 12. Double-B usage

Double-B remains useful in V8 because it is an objective rare-event anchor with substantial prior project
research.

But V8 explicitly permits decisions after common events too, for example:

```text
Double-B
→ price extends
→ pullback reaches MA
→ new causal chart observation
→ HOLD / ADD / EXIT decision
```

or:

```text
position already profitable
→ price reaches MA / equilibrium area
→ new causal chart observation
→ REDUCE / HOLD decision
```

The new decision does not require the system to label the whole market `BREAKOUT` or `BASIC`.

## 13. Frequency

High frequency is pursued by allowing repeated **legitimate decision opportunities**, not by loosening one
entry filter until it fires constantly.

Report separately:

- event anchors/day;
- decision opportunities/day;
- initial entries/day;
- add actions/day;
- reductions/day;
- exits/day;
- campaigns/day.

This distinction is mandatory.

## 14. First implementation acceptance tests

Before opening P/L:

- renderer is deterministic;
- same timestamp produces identical chart bytes;
- no future bar can appear;
- event marker timing is causal;
- visual and numerical final timestamps match;
- resampling uses only completed bars;
- campaign state agrees with replay log;
- source data hash is recorded;
- a human can inspect a random sample and confirm the rendered panel corresponds to the raw source.

Only after these pass may V8-001B open future outcomes for representation diagnostics.
