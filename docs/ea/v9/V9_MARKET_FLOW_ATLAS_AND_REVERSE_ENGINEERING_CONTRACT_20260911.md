# V9 Market Flow Atlas + Reverse-Engineering Contract

Date: `2026-09-11`
Status: `ACTIVE NEXT V9 CONTRACT / ANSWER-SHEET MARKET-FLOW RESEARCH`
Market: `GOLD# ONLY`
Production authority: `NONE`
EA authority: `NONE`

Consumed development data:

- `2025-01 through 2025-06`
- `2026-01 through 2026-02`

Future-hidden:

- `2025-07 LOCKED`

Untouched final reserve:

- `GOLD# 2021`

## Purpose

Stop improving one trade at a time before the strategy grammar is understood.

Use already-consumed data as an answer sheet and study the continuous market flow:

```text
reaction / arrival
-> price delivery
-> next reaction / arrival
-> price delivery
-> ...
```

Do not search for a perfect deterministic market law.
Build a small reusable analysis grammar that remains useful across trends, ranges, repairs, false breaks, liquidity raids, and noisy transitions.

## Research mode

Full-history / future-visible analysis is allowed on consumed development data only.

This phase is noncausal research.

Therefore:

- do not call results validation;
- do not report hindsight trades as strategy performance;
- do not backfill the official trading record;
- do not use `2025-07` or `2021`;
- preserve timestamps and object provenance so the extracted grammar can later be tested causally.

Causal replay returns only after the flow grammar and strategy extraction are stable enough to test.

## Research unit

The primary unit is not a trade.

Use:

```text
FLOW LEG
AUCTION CYCLE
REACTION / ARRIVAL EVENT
DELIVERY PATH
DESTINATION / NEXT STATE
```

Price does not need to move vertex-to-vertex.

Treat these as first-class states:

- directional migration;
- repair;
- balance / range;
- compression;
- expansion;
- false break;
- liquidity sweep / raid;
- shakeout / stop-run-like behavior;
- failed POI response;
- acceptance through an old POI;
- transition into a new auction.

## Analysis lenses

Use tools to make the chart legible.
Do not convert every tool into a signal.

### Deterministic market objects

Continue using exact mechanical candidates for:

- FVG;
- OB candidate;
- swing / liquidity candidate;
- object birth, touch, fill, raid, mitigation, invalidation.

These provide coordinates and lifecycle.
They do not provide strategic importance.

### Structural / auction lenses

Study:

- displacement;
- acceptance / rejection;
- range boundaries;
- compression / expansion;
- liquidity delivery;
- failed breaks;
- sweep / shakeout behavior;
- fresh versus stale campaign structures;
- internal versus external destination;
- migration versus repair versus balance.

### Indicator / statistical lenses

Indicators may be used as research lenses, including:

- MACD;
- Bollinger Bands;
- moving-average structure;
- ATR / volatility;
- momentum / rate-of-change;
- session / time-of-day context.

No indicator has authority merely because it is familiar.

Keep an indicator only when it repeatedly helps distinguish or compress market flows across many examples.
Reject explanations that work only after the outcome is known.
Do not build an indicator stack that gives every move a different story.

## Atlas record

For every meaningful continuous leg record:

```text
LEG_ID
START_TIME / START_PRICE
END_TIME / END_PRICE
DIRECTION / STATE
ORIGIN EVENT
ORIGIN OBJECT IDS
PRE-LEG MARKET STATE
MOVEMENT POINTS / S / DURATION
INTERMEDIATE OBJECTS CREATED
INTERMEDIATE LIQUIDITY EVENTS
DESTINATION / ARRIVAL EVENT
END-STATE
NEXT LEG ID
USEFUL ANALYSIS LENSES
AMBIGUITY / COUNTEREXAMPLE NOTES
```

Ranges and balances may be recorded as time-spanning states rather than a single directional leg.

## Research process

1. Build long contiguous H4/H1 maps. Include trends, ranges, noise, false breaks, and ambiguous periods.
2. Overlay deterministic FVG / OB / liquidity objects.
3. Describe what price did before explaining why.
4. Add indicator/statistical lenses only when they materially clarify repeated flows.
5. Cluster many legs into a small number of reusable flow archetypes.
6. Merge archetypes when one broader relationship explains both.
7. Stress the same grammar across different market conditions.
8. Keep counterexamples and unresolved remainder visible.

Possible archetypes are hypotheses, not preset truth:

```text
liquidity delivery -> opposing POI response -> repair
displacement -> fresh continuation POI -> retracement -> further delivery
POI failure / acceptance -> old thesis retired -> next array
liquidity raid -> weak rejection -> continuation to next external liquidity
balance -> liquidity probe -> acceptance / failed breakout -> expansion
```

Prefer:

```text
many flows -> small reusable grammar + explicit ambiguous remainder
```

over:

```text
100 moves -> 100 special explanations
```

## Outputs

Build a `V9 Market Flow Atlas` containing:

- continuous annotated H4/H1 flow maps;
- exact object-ledger links;
- leg / state table;
- repeated-flow archetype catalogue;
- representative examples and counterexamples;
- indicator-lens usefulness notes;
- unresolved ambiguous flows;
- candidate market-flow grammar.

Suggested artifacts:

```text
FLOW_LEG_LEDGER.csv
FLOW_STATE_LEDGER.csv
FLOW_ARCHETYPE_CATALOG.md
LENS_EVIDENCE_LEDGER.csv
ATLAS_CHARTS/
```

Trade count, win rate, and R are not the optimization target in this phase.

## Strategy extraction comes later

After the atlas stabilizes, reverse-engineer the tradable subset.

Ask:

```text
Which flow state is knowable in real time?
Which arrival can be planned before it happens?
Which response is observable before paying risk?
Which Child invalidation is objective?
Which part of the next delivery is realistically capturable?
Which flows should be ignored?
```

Only then define H4 Parent, H1 auction loop, trigger, LTF execution, Hard SL, journey review, trailing/exit, and AI-call events.

## Anti-overfit

Do not create:

- one rule per chart example;
- fixed indicator thresholds because they explain a few moves;
- mandatory FVG + OB + sweep + BOS chains;
- fixed retracement depth;
- fixed trade-frequency targets;
- fixed R / S targets;
- hindsight-only object labels;
- special exceptions that only rescue failed examples.

The target is a robust discretionary analysis grammar, not perfect prediction.

## Exit criteria

Do not return to strategy-performance optimization until:

1. long contiguous consumed periods are mapped rather than cherry-picked;
2. trends, ranges, repairs, sweeps, and failures are represented;
3. a small set of flow relationships explains a meaningful share of the atlas;
4. the same relationship is recognizable across different months without changing its definition;
5. useful indicators add stable discrimination rather than post-hoc stories;
6. object provenance and lifecycle remain exact;
7. contradictions and ambiguous flows are retained;
8. the candidate grammar is simple enough to convert into a real-time decision process.

Then freeze a strategy-extraction draft and return to causal replay.

## Research order

```text
CONSUMED FULL-HISTORY FLOW ATLAS
-> REPEATED FLOW RELATIONSHIPS
-> MINIMAL MARKET-FLOW GRAMMAR
-> STRATEGY EXTRACTION
-> CAUSAL SEQUENTIAL REPLAY
-> LIVE AI-CALL / MT5 / RUNTIME DESIGN
-> FUTURE-HIDDEN REPLAY
```

Do not open July before the downstream causal gate passes.
