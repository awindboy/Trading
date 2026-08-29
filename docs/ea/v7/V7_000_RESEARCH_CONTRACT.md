# V7-000 Research Contract

Status: `ACTIVE PRE-VALIDATION CONTRACT`
Date: `2026-08-30`
Production authority: `NONE`

## Research question

Can a trader/AI, with future bars hidden, use the Kim Jikseon-style
Double-B + context + KTR framework to distinguish:

- fresh directional expansion,
- range-extreme mean reversion,
- terminal/exhaustion expansion,
- and situations that should simply be waited on or skipped,

well enough to produce a positive, robust trading process?

## Why V7 exists

V1-V6 showed that increasingly detailed deterministic pattern/routing systems can look strong
on consumed data and still fail external validation.

V7 therefore starts from a different premise:

> A rare chart event may identify **when information content is high**, while the trade direction
> and risk plan may depend on contextual meaning that cannot always be faithfully reduced to
> one fixed indicator score.

V7 does not assume discretionary interpretation is superior.
It tests that proposition under blinded, auditable conditions.

## Research objects

### Event
An H1 Double-B occurrence.

### Decision record
Locked before future reveal:
- ENTER_NOW / WAIT_CONFIRM / SKIP;
- LONG / SHORT if actionable;
- BASIC / BREAKOUT / TURNING / UNKNOWN;
- evidence table;
- KTR value and relevant session;
- structural invalidation;
- SL in price and KTR;
- target room in price and KTR;
- staged-entry plan or no-staging;
- maximum allowed legs;
- confidence and uncertainty.

### Outcome record
Added only after the decision record is locked.

## Primary evidence hierarchy

1. blinded untouched validation;
2. repeated blinded discovery on separate cohorts;
3. outcome-informed reverse engineering;
4. automated proxy backtests.

A good proxy backtest cannot overrule a failed blinded contextual test.

## Current consumed discovery set

24 Double-B events:
- 8 GOLD#,
- 8 BTCUSD#,
- 8 USDJPY#,
- balanced upper/lower within each market.

These events were first used for a blind visual pilot and then opened for hindsight reverse engineering.

They are permanently consumed.

## Prohibited research behavior

- no same-event hindsight correction counted as validation;
- no global KTR threshold extracted from a few winning hindsight examples;
- no treating outside-band close as automatic breakout;
- no adding discretionary variables only because they separate winners in the consumed 24;
- no P/L-based event deletion;
- no market selection after seeing V7 P/L;
- no unlogged second trade after a failed first thesis;
- no ambiguous WAIT case retrospectively relabeled as a perfect immediate entry.

## Minimum next validation design

Before outcome reveal:
1. freeze event population;
2. freeze visual inputs;
3. freeze decision form;
4. record decisions for the full batch;
5. hash/save decision ledger;
6. only then reveal M1/H1 future path.

Report:
- trade count;
- skip/wait rate;
- direction accuracy;
- archetype confusion;
- campaign WR;
- campaign EV;
- average positive R;
- total filled legs;
- risk-normalized campaign return;
- DD;
- loss streak;
- results by market;
- results by archetype;
- calibration by confidence.

No production EA implementation until this process demonstrates repeatability.
