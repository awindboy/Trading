# V9 Research Instructions — Current Authority

Last synchronized: `2026-09-11`
Status: `ACTIVE / MARKET-FLOW ATLAS + REVERSE ENGINEERING`
Production authority: `NONE`
EA authority: `NONE`
Market: `GOLD# ONLY`
Consumed development data: `2025-01 through 2025-06`, `2026-01 through 2026-02`
Future-hidden: `2025-07 LOCKED`
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
6. `V9_MARKET_FLOW_ATLAS_AND_REVERSE_ENGINEERING_CONTRACT_20260911.md`
7. `V9_CHART_NATIVE_ICT_OBJECT_AND_MTF_PIPELINE_20260910.md`
8. `V9_CAUSAL_NUMERIC_ANALYSIS_AND_TOOLING_PROTOCOL_20260910.md`
9. `V9_DISCRETIONARY_TRADING_PIPELINE_POSTJUNE_20260910.md`
10. `V9_NEXT_RESEARCH_CONTRACT_POSTJUN_EXECUTION_RUNTIME_20260910.md`
11. current code/tool parity state.

The Market Flow Atlas contract is the active research contract.
Sequential causal trading is downstream until strategy extraction.

## Current research identity

Use consumed data as an answer sheet:

```text
REACTION / ARRIVAL
-> PRICE DELIVERY
-> NEXT REACTION / ARRIVAL
-> PRICE DELIVERY
-> ...
```

Study continuous H4/H1 flow before optimizing trades.

Primary research units:

```text
FLOW LEG
AUCTION CYCLE
BALANCE / RANGE STATE
DELIVERY PATH
DESTINATION / NEXT STATE
```

Ranges, compression, false breaks, liquidity raids, and noisy transitions are first-class states.

## Analysis toolkit

Code owns exact FVG / OB / swing-liquidity geometry and lifecycle.
AI owns semantic market interpretation.

Allowed research lenses include:

- ICT POI / FVG / OB / liquidity;
- displacement / acceptance / rejection;
- balance / range / compression / expansion;
- MACD;
- Bollinger Bands;
- moving averages;
- ATR / volatility;
- momentum / rate-of-change;
- session/time context.

These are lenses, not automatic signals.

Keep only concepts that repeatedly help explain many flows.
Do not attach a different story or indicator to every move.

## Current research mode

Full future-visible analysis is allowed only on already-consumed development data.

This mode is noncausal.
Do not present it as validation or strategy performance.
Do not backfill hindsight trades.

Never use `2025-07` or `2021`.

Preserve exact timestamps and object provenance so the candidate grammar can later be tested causally.

## Research objective

Build a `V9 Market Flow Atlas`.

Map long contiguous windows and record:

- where price arrived;
- what it consumed;
- what state preceded the move;
- where price delivered;
- what objects were created;
- what changed the state;
- what the next leg did.

Search for the smallest reusable market-flow grammar.

Prefer:

```text
many flows -> few reusable relationships
```

over:

```text
one special explanation per chart
```

Keep ambiguous and contradictory cases.

## Indicators

Do not promote MACD, Bollinger Bands, or another indicator into authority because a few examples fit.

No fixed indicator threshold is authorized.

## Strategy extraction

Do not optimize Entry, SL, TP, trigger, trade frequency, or AI-call cadence while the market-flow grammar is unstable.

After the atlas phase:

```text
FLOW GRAMMAR
-> REAL-TIME KNOWABLE STATE
-> TRADABLE SUBSET
-> H4 PARENT / H1 AUCTION
-> LTF EXECUTION
-> HARD SL / JOURNEY
-> CAUSAL REPLAY
```

Retain:

- Parent / Child separation when trading research resumes;
- Hard SL before entry;
- no widening;
- no hindsight rescue;
- no minimum-R;
- no fixed ATR/S stop or TP;
- no cooldown;
- no retry cap;
- no forced side balance;
- no mandatory ICT pattern chain;
- no fixed trade-frequency target.

## Causal integrity

Current atlas work is intentionally noncausal on consumed data.

When causal replay resumes:

- use only revealed chronological prefix;
- freeze events before resolution;
- never rescue a stopped Child;
- record accidental reveal and never backfill.

Do not open July before the downstream causal gate passes.
