# V9 Research Instructions — Current Authority

Last synchronized: `2026-09-10`
Status: `ACTIVE / SEQUENTIAL CHART-NATIVE MAP-TRIGGER-POSITION RESEARCH`
Production authority: `NONE`
EA authority: `NONE`
Market: `GOLD# ONLY`
Consumed development data: `2025-01 through 2025-06`
Next future-hidden candidate: `2025-07 — LOCKED`
Untouched final reserve: `GOLD# 2021`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`

## Resume order

Start from latest GitHub `main` HEAD.

Read:

1. `AGENTS_V9.md`
2. `HANDOFF_V9.md`
3. `RESEARCH_STATE_V9.md`
4. `V9_TRADING_MINDSET_AND_RESEARCH_GUARDRAILS_20260907.md`
5. `DECISIONS_V9_POSTJUNE_SIMPLIFICATION_AND_RUNTIME_ADDENDUM_20260910.md`
6. `V9_CHART_NATIVE_ICT_OBJECT_AND_MTF_PIPELINE_20260910.md`
7. `V9_DISCRETIONARY_TRADING_PIPELINE_POSTJUNE_20260910.md`
8. `V9_NEXT_RESEARCH_CONTRACT_POSTJUN_EXECUTION_RUNTIME_20260910.md`
9. `V9_CAUSAL_NUMERIC_ANALYSIS_AND_TOOLING_PROTOCOL_20260910.md`
10. current code/tool parity state before any new future-hidden reveal.

Use `results/V9_ICT_OBJECT_ENGINE_AND_MTF_TRIGGER_CALIBRATION_20260910.md` as current consumed-data evidence.
Treat older postmortems and pipelines as historical evidence when they do not conflict with current authority.
Treat deterministic-order/scheduler documents as deferred implementation references.

Do not open July before the active contract passes.

## Strategy identity

Use:

```text
CAUSAL HTF MARKET MAP
-> MECHANICAL ICT CANDIDATE UNIVERSE
-> AI SELECTS MAJOR POI / LIQUIDITY / ROUTE
-> WAIT
-> SELECTED HTF EVENT
-> LTF TRIGGER MANAGEMENT
-> CHILD ENTRY + HARD SL
-> MULTI-HOUR / MULTI-S JOURNEY
-> HOLD / EXIT / REMAP
```

Read the large structure first.
Do not start from the current candle or nearest LTF setup.

## Object authority

Code creates exact candidate geometry and lifecycle.

Current candidate families:

- H4/H1 FVG;
- H4/H1 OB candidate;
- H4/H1 swing/liquidity candidate.

Code records source candle(s), exact price range, born time, touch/mitigation/fill/raid/invalidation time.

Code does not decide strategic importance.

AI selects which objects matter in the current H1/H4 map.
AI must select existing object IDs for official POI/liquidity coordinates whenever an applicable candidate exists.
Do not let AI silently move an object's geometry.

Keep geometric lifecycle separate from strategic lifecycle.

```text
geometrically active != strategically important
Child stop != HTF object death
FVG full fill -> FVG geometric end
liquidity raid -> liquidity geometric end
```

## Two-chart research packet

Use exactly two AI-facing chart roles:

```text
MAP
TRIGGER
```

MAP:

- H1 main chart;
- selected H4/H1 objects overlaid;
- major liquidity and route;
- Entry/SL/review levels when relevant.

TRIGGER:

- M5 by default;
- M15 when the active trigger is clearly M15-scale;
- open only after an HTF POI/liquidity event makes LTF relevant;
- otherwise treat trigger state as `INACTIVE`.

Keep chart annotations short and out of the price structure.

## AI role

AI decides:

1. large H1/H4 market structure;
2. which candidate objects matter now;
3. major POIs and external liquidity;
4. LONG scenario and strongest SHORT scenario;
5. `WAIT`, trigger preparation, entry, or remap;
6. which objective LTF event is worth using as a trigger;
7. which structure invalidates the Child at the intended scale;
8. which HTF structures are destination or review points;
9. at authorized review: `HOLD / EXIT / REMAP`.

Do not turn every FVG, OB, swing, sweep, BOS, or CHOCH into a signal.

## Runtime/code role

Code handles:

- fail-closed causal M1 reveal;
- H4/H1/M15/M5 construction;
- ICT candidate object generation;
- exact coordinates and lifecycle timestamps;
- chart rendering;
- frozen event monitoring;
- Entry/SL/R/S arithmetic;
- Hard SL guards;
- selected destination/review touches;
- MFE/MAE and journal timestamps.

## Parent and Child

Parent is the large working map and journey.
Child is one paid attempt.

Retain:

```text
Child stop != Parent death
Child win != Parent proof
Parent survival != automatic re-entry
later movement cannot rescue a stopped Child
```

For retry ask:

```text
WHAT OBJECTIVE FACT CHANGED?
IS THIS A GOOD PITCH?
```

## Entry and trigger

Prioritize HTF map and POI quality over LTF precision.

Do not enter because price touched a POI.
Observe the selected POI interaction.
Freeze the objective LTF trigger condition before advancing to it.

LTF improves execution.
LTF does not create an unrelated Parent thesis.

Do not chase a missed move.
`NO TRADE` because the selected POI never arrived is a valid outcome.

## Hard SL

Set Hard SL before entry.
Never widen it.

Place SL where the current Child is actually wrong at the intended scale.

Do not select SL from fixed points, ATR, R, S, or desired payoff.
Do not use a tiny LTF structure merely because it improves R.
Do not use the full Parent failure level merely to survive noise.

## TP and journey

Use major HTF structures and external liquidity for route and review.

Parent-Journey may use `FIXED TP = NONE`.
Nearby LTF structure is transit unless it resolves the thesis.

Use prior completed H4 Wilder ATR14 as `S` for scale measurement only.
Measure meaningful `1S+`, `2S+` winner participation without making S a fixed target.

## Sequential research behavior

Do not reanalyze from a blank slate on every call.
Persist the prior market-map ledger and object roles.

Advance price only to frozen events.
At each event:

```text
update geometric object states
show current MAP
show TRIGGER only if relevant
state MAP CHANGES
then WAIT / ENTER / HOLD / EXIT / REMAP
```

Do not call AI on every candle.
During current research, extra calls are allowed only when explicitly testing map-update behavior; label them research-only.

## Causal integrity

Use only revealed chronological prefix.
Never backfill after future exposure.
Never rescue a stopped Child.

```text
2025-01 through 2025-06 = CONSUMED DEVELOPMENT
2025-07 = FUTURE-HIDDEN / LOCKED
2021 = UNTOUCHED FINAL RESERVE
```

## Anti-overfit

Do not add:

- minimum R;
- fixed ATR/point/S SL or TP;
- N-loss cooldown;
- retry limit;
- fixed no-chase distance;
- forced LONG/SHORT balance;
- fixed hold/retest counts;
- mandatory indicator rules;
- mandatory ICT-pattern chains;
- deterministic major/minor strategic labels.

Do not change authority from one or two examples.
Use consumed data for repeated replay and failure study first.
