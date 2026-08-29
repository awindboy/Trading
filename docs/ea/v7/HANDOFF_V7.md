# V7 Development Handoff

Last updated: `2026-08-30`
Current GitHub base for this update: `3c35cdc72b9f6046de716cd0d956a918021eba1e`
Current phase: `V7-003A GOLD25/BTC25 DOUBLE-B ANATOMY DISCOVERY`
Production authority: `NONE`
EA authority: `NONE`
Untouched reserve: `GOLD 2021`

## Current thesis

V7 does not start from a fixed entry rule.

```text
rare Double-B event
-> understand event type
-> understand context
-> understand KTR-scaled path geometry
-> choose entry architecture
-> choose risk/staging only after the thesis exists
```

Core meaning problem:

```text
FRESH EXPANSION
RANGE EXTREME
TERMINAL EXPANSION
INSUFFICIENT / CHAOTIC INFORMATION
```

These may later map to `BREAKOUT / BASIC / TURNING / WAIT-SKIP`.

## Frozen development cohort

```text
GOLD# 2025
BTCUSD# 2025
```

Outcome opening is allowed and expected.
These market-years are development data and cannot later serve as untouched validation.

Do not add Nasdaq, Oil, other years, or extra symbols to improve apparent results.

## Why reverse engineering comes before validation

Immediate blind validation is premature because:
- many method components interact;
- the 24-event pilot showed the AI does not yet read context reliably;
- hindsight work showed direction, target, KTR use and staging are separate problems;
- weak formalization can become a different strategy.

## Research sequence

### V7-003A — Double-B Anatomy — CURRENT
Census all GOLD25/BTC25 events and study pre/event/post anatomy.
No strategy optimization.

### V7-003B — Context Atlas
Session -> S/R -> Bollinger -> candle -> MA maturity -> trendline if needed.

### V7-003C — KTR Geometry
Study normalized path, structural invalidation and target room.
No fixed-multiple tournament.

### V7-003D — Entry Architecture
Immediate vs planned pullback/zone vs wait-confirm vs skip.

### V7-003E — Staging / Campaign Risk
Only after a single-entry baseline and normal adverse excursion are understood.

### V7-003F — Decision Rubric Freeze
Convert recurring discovery into a causal pre-outcome process.

### V7-004 — Untouched Blinded Validation
Use a separate untouched cohort only after V7-003F.

## First next-session deliverable

Create:
`V7_003A_GOLD25_BTC25_DOUBLEB_ANATOMY_LEDGER`
plus a companion result document.

Before analysis:
- verify raw M1;
- log SHA256 and coverage;
- log server/time convention;
- verify OHLC/spread integrity;
- derive H1;
- detect all Double-B events;
- save the complete census.

Then open outcomes and characterize every event.

## Do not optimize trades in V7-003A

Do not:
- maximize R;
- choose best SL/TP;
- search best KTR multipliers;
- add ladders;
- delete difficult/ambiguous events;
- assign a trade to every event;
- force exactly three archetypes.

## Context topics that must be learned

- Double-B anatomy: fresh expansion vs range extreme vs terminal expansion vs noise.
- Candle: acceptance vs rejection vs climax.
- Bollinger: BB20/BB4 compression, expansion, divergence and maturity.
- Session: opening-H1 break, wick, acceptance, failure and reclaim.
- S/R: range edge, fresh structure, nearby barrier, remaining room.
- MA: direction plus maturity/extension, not simple above/below.
- KTR: structural distance and realistic room in current session units.

## Trendline

Trendline is part of the remembered framework but deferred.
If it cannot be assessed faithfully, record `UNKNOWN` rather than inventing a proxy.

## Consumed evidence

The original V7-002 24-event set remains consumed.
The +89.03R hindsight plan is not validation.

GOLD25/BTC25 will also be consumed once V7-003 outcome work begins.

## Hard restrictions

- no V7 EA;
- no production claim;
- no same-data validation;
- no forced additive score;
- no fixed KTR table from discovery outcomes;
- no staging optimization before single-entry/event anatomy;
- no V6 rule import;
- no market expansion after observing P/L.

Read next:
`V7_003A_GOLD25_BTC25_DEVELOPMENT_PLAN.md`.
