# V9 Research Instructions — Current Authority

Last synchronized: `2026-09-10`
Status: `ACTIVE / CHART-NATIVE HTF MARKET-MAP RESEARCH`
Production authority: `NONE`
EA authority: `NONE`
Market: `GOLD# ONLY`
Consumed development data: `2025-01 through 2025-06`
Next future-hidden candidate: `2025-07 — LOCKED`
Untouched final reserve: `GOLD# 2021`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`

## Resume order

Start from latest GitHub HEAD.

Read:

1. `AGENTS_V9.md`
2. `HANDOFF_V9.md`
3. `RESEARCH_STATE_V9.md`
4. `V9_TRADING_MINDSET_AND_RESEARCH_GUARDRAILS_20260907.md`
5. `DECISIONS_V9_POSTJUNE_SIMPLIFICATION_AND_RUNTIME_ADDENDUM_20260910.md`
6. `V9_DISCRETIONARY_TRADING_PIPELINE_POSTJUNE_20260910.md`
7. `V9_NEXT_RESEARCH_CONTRACT_POSTJUN_EXECUTION_RUNTIME_20260910.md`
8. `V9_CAUSAL_NUMERIC_ANALYSIS_AND_TOOLING_PROTOCOL_20260910.md`

Treat June postmortems as historical evidence.
Treat deterministic-structure-runtime and precommitted-scheduler documents as deferred implementation references.

Do not open July before the active research contract passes.

## Strategy identity

Use:

```text
HTF MARKET MAP
-> MAJOR POI / EXTERNAL LIQUIDITY
-> LONG / SHORT SCENARIOS
-> WAIT
-> LTF EXECUTION
-> HTF-ALIGNED HARD SL
-> MULTI-HOUR / MULTI-S JOURNEY
```

Read the large structure first.
Do not start from the current candle or nearest setup.

## Chart-native analysis

Use chart images as a primary AI input.
Use raw OHLC and numeric packets as supporting facts.

Default research view:

- H1: show enough history to contain the active multi-day legs. Use about 7-15 trading days as a display default, not a trade filter.
- H4: show broader context when earlier structure matters.
- LTF: open only after the HTF map and scenario are clear.

Mark:

- major directional legs;
- major swing highs/lows;
- external liquidity candidates;
- major POIs;
- range edges;
- compression boundaries;
- displacement origins;
- consumed and still-relevant structure;
- large routes in both directions.

Do not force a deterministic swing algorithm to decide which structure matters.

## AI role

AI decides:

1. the large H1/H4 market structure;
2. which highs/lows and zones matter now;
3. major POIs;
4. meaningful external liquidity candidates;
5. expansion, pullback, range, edge, or compression state;
6. LONG scenario;
7. SHORT scenario;
8. which scenario offers a good pitch;
9. which structure invalidates the Child at the intended scale;
10. which HTF structures are destination or review points.

Do not turn every swing, FVG, OB, sweep, BOS, or CHOCH into a signal.

## Code/runtime role

Code handles:

- causal chart construction;
- exact coordinates after AI selection;
- Entry/SL distance;
- R and S;
- prepared-order monitoring;
- Hard SL guards;
- selected destination/review touches;
- MFE/MAE;
- timestamps;
- replay state.

Code does not assign strategic importance because a mechanical swing rule detected a structure.

## Parent and Child

Parent is the large working market map and journey.
Child is one paid attempt inside that map.

Retain:

```text
Child stop != Parent death
Child win != Parent proof
Parent survival != automatic re-entry
later movement cannot rescue a stopped Child
```

For retry ask:

`WHAT OBJECTIVE FACT CHANGED?`

Then ask:

`IS THIS A GOOD PITCH?`

## Entry

Prioritize HTF structure quality over LTF entry precision.

Do not optimize LTF entry until HTF mapping is reliable.

After the HTF map matures, use H1/M15/M5 to improve execution location and timing.

Do not chase a missed entry.

## Hard SL

Set Hard SL before entry.
Never widen it.

Place SL where the current Child is actually wrong at the intended scale.

Do not give a tiny LTF fluctuation full stop authority unless losing it invalidates the Child.
Do not use the full Parent failure level when a nearer structure already invalidates the Child.

Do not derive SL from fixed points, ATR, R, S, or a desired payoff multiple.

## TP and journey

Aim to capture meaningful market movement.

Use major HTF structure and external-liquidity candidates for destination and review planning.
Treat nearby LTF structure as transit unless it resolves the thesis.

Parent-Journey may use `FIXED TP = NONE`.
At major HTF structure decide `HOLD / EXIT / REMAP`.

Use prior completed H4 ATR14 as `S`.
Use S as a scale measurement.
Do not use S as a fixed target or stop formula.

Measure whether winners capture `1S+`, `2S+`, and larger journeys.

## Direction

Evaluate LONG and SHORT from the same map.
Parent is not a direction veto.
State the strongest opposite scenario.

Do not force side balance.

## Causal integrity

Use only revealed chronological prefix in future-hidden replay.
Never backfill after future exposure.
Never rescue a stopped trade with later price.

```text
2025-01 through 2025-06 = CONSUMED DEVELOPMENT
2025-07 = FUTURE-HIDDEN / LOCKED
2021 = UNTOUCHED FINAL RESERVE
```

## Anti-overfit

Do not add:

- minimum R;
- fixed ATR/point SL or TP;
- N-loss cooldown;
- retry limit;
- fixed no-chase distance;
- forced LONG/SHORT balance;
- fixed hold/retest bar counts;
- mandatory indicator rules;
- mandatory ICT-pattern chains;
- deterministic major/minor labels without evidence.

Research the market map first.
Formalize execution later.
