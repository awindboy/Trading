# V8 Development Handoff

Last updated: `2026-08-30`
GitHub base: `fb9c97cb358b170cba32f0f2b68de5ecb8968794`
Current phase: `V8-001A CAUSAL CHART REPRESENTATION FOUNDATION`
Production authority: `NONE`
EA authority: `NONE`
Market: `GOLD# only`
Untouched reserve: `GOLD# 2021`

## Why V8 was opened

The decisive V8 insight is representational.

Recent research repeatedly tried to convert chart context into explicit states such as trend, range,
breakout, turning, healthy pullback or terminal expansion. The user correctly identified that these states
are not uniquely observable objects. A numerical threshold may be exact while the semantic interpretation is
still wrong.

The project therefore stops treating ambiguous human chart concepts as mandatory hard labels.

V8 thesis:

```text
objectively observable event
+ causal chart geometry
+ exact numerical state
+ current campaign state
        ↓
learned latent context
        ↓
action-conditioned path / policy
```

The model does not need to say `this is a breakout` before it can decide whether entering, waiting, adding,
holding, reducing or exiting has value.

## Current data available outside the repository

Unified GOLD# M1 file:

```text
GOLD#_M1_202201030100_202608282357.csv
SHA256: 626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2
bytes: 101405198
data rows: 1648545
coverage: 2022-01-03 01:00:00 through 2026-08-28 23:57:00
```

This file is V8 open development evidence.

It is not a pristine holdout because 2022-2026 have already been inspected by prior/current research.

Do not commit the raw file to Git unless the repository data policy is explicitly changed.

## First concrete task

Create `V8-001A` representation infrastructure before any new P/L tournament.

Required first deliverables:

1. causal multi-timeframe bar builder for H1/M15/M5/M1;
2. deterministic chart renderer;
3. visual/numerical timestamp parity audit;
4. causal Bollinger/MA/event overlays;
5. event-anchor ledger;
6. campaign-state schema;
7. strict no-future rendering tests;
8. data manifest with source identity;
9. sample chart retrieval pack for human inspection.

The first milestone is **representation correctness**, not profitability.

## Initial chart panels

Start with:

```text
H1
M15
M5
M1
```

Do not outcome-tune the lookback lengths at this stage.

Use windows long enough to show qualitatively different context scales, then freeze those window lengths
before economic comparison.

## Event-anchor principle

An event is allowed to be simple and frequent.

Examples:

- Double-B confirmation;
- MA interaction;
- Bollinger interaction;
- session boundary interaction;
- causal S/R interaction;
- displacement/activity event.

The important question is not whether the event itself predicts direction.

The question is whether the **current chart representation surrounding that event** changes the value of
possible actions.

## No forced archetype classification

V8 may still use the words:

```text
BASIC
BREAKOUT
TURNING
```

when a human describes retrieved examples.

They are explanatory vocabulary only.

Do not make them required labels, rule gates, or supervised targets in the base V8 system.

## Campaign objective

V8 must be able to represent scenarios such as:

```text
initial entry
→ continuation
→ pullback to MA
→ ADD or HOLD or EXIT based on the new chart
→ partial realization
→ runner
→ later reduction/exit
```

This is not duplicate-trade counting.

Every action belongs to one campaign with explicit total exposure and risk accounting.

## Research order

### V8-001A — CURRENT
Representation and causal renderer.

### V8-001B
Event-anchor census and latent-retrieval diagnostics. No tuned trading controller yet.

### V8-002
Compare:
- raw/numerical-only encoder;
- visual-only encoder;
- fused visual+numerical encoder;
- hand-engineered scalar baseline.

Test information value before controller complexity.

### V8-003
Action-conditioned future path model.

### V8-004
Sequential campaign policy with spread/cost/exposure accounting.

### V8-005
Freeze candidate and evaluation protocol.

### V8-006
Untouched GOLD# 2021 validation.

## Validation discipline

2022-2026 may be split chronologically for development diagnostics, but none of those years regain pristine
validation status.

Do not repeatedly optimize on later development years until a target metric passes.

The final untouched claim remains reserved for GOLD# 2021.

## First failure conditions

V8 should be considered falsified or redirected if:

- visual/fused representation does not beat same-information scalar/numerical baselines in future-hidden tests;
- retrieved latent neighbors are unstable and economically uninformative;
- action-conditioned estimates collapse after sequential non-overlap/campaign accounting;
- apparent edge depends on repeated decisions inside one move being counted independently;
- full-cost expectancy disappears under realistic spread;
- performance is carried by one narrow year/session without a preregistered structural reason.

## Immediate reading order next session

1. `docs/ea/v8/AGENTS_V8.md`
2. `docs/ea/v8/HANDOFF_V8.md`
3. `docs/ea/v8/V8_000_RESEARCH_CONTRACT.md`
4. `docs/ea/v8/V8_001_REPRESENTATION_AND_POLICY_SPEC.md`
5. `docs/ea/v8/DECISIONS_V8.md`
6. `docs/ea/v8/RESEARCH_STATE_V8.md`

Then verify latest GitHub HEAD before doing any implementation or analysis.
