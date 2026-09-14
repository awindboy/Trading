# V9 Prototype Authority

Date: `2026-09-14`
Status: `CURRENT RESEARCH PROTOTYPE AUTHORITY / NOT PRODUCTION AUTHORITY`
Market: `GOLD# ONLY`

## 1. Purpose

This document consolidates the surviving V9 mechanics after full-era M1 research, ERA4 normalization, role-based Child management, and MT5 actual-tick validation.

Where older strategy-semantic documents conflict with this document, this document wins. Generic causal tooling rules remain in force unless explicitly superseded by the current tick/ERA addendum.

## 2. Market objects

H1 and H4 liquidity use causal two-left / two-right swing geometry.

A swing becomes usable only after the second right bar is complete. An active level remains active until causally raided.

H4 liquidity is the delivery/progression object. H1 liquidity is the structural-invalidation object for the Child.

## 3. Tick-native Arrival semantics

For execution-grade replay, Bid tick chronology owns liquidity-raid ordering.

Each distinct H4 liquidity raid reached on a distinct tick is a distinct Arrival. Do not merge later same-minute raids using the eventual M1 high/low.

If both directions are genuinely unresolved at the same executable instant, remain unresolved; do not invent a favorable ordering.

M1 aggregation remains useful for reconstruction and historical comparison but does not own intraminute execution order.

## 4. Grammar

```text
initial directional H4-liquidity Arrival
-> SEED primary side
-> PRIMARY_ACTIVE(side)

PRIMARY_ACTIVE(A) + same-side H4 liquidity
-> PRIMARY_CONTINUES(A)

PRIMARY_ACTIVE(A) + opposite H4 liquidity B
-> CHALLENGE_OPENS
-> CHALLENGED(A,B)

CHALLENGED(A,B) + old-primary side A
-> OLD_PRIMARY_WINS
-> PRIMARY_ACTIVE(A)

CHALLENGED(A,B) + challenger side B
-> CHALLENGER_EARNED
-> PRIMARY_ACTIVE(B)
```

CHALLENGED is unresolved for new directional authorization until a resolver Arrival earns PRIMARY_ACTIVE again.

## 5. Structural Hard SL

At authorized Child entry:

```text
LONG  -> highest active causally-known H1 SSL strictly below entry
SHORT -> lowest active causally-known H1 BSL strictly above entry
```

No valid opposite H1 structure -> no Child.

Hard SL is fixed before entry and never widened. A stopped Child is dead.

## 6. Era-scale eligibility

```text
ERA_SCALE(t) = previous fully completed H4 Wilder ATR180
ERA_RISK     = abs(execution-reference entry - structural SL) / ERA_SCALE(t)
```

Current prototype eligibility:

```text
ERA_SCALE available
AND valid causal H1 structural SL
AND ERA_RISK <= 4
```

If `ERA_RISK > 4`, do not enter. Do **not** move the structural stop inward to `4 x ATR180`.

ATR14 may remain a fast descriptive coordinate but has no current entry-threshold authority.

## 7. Child roles

A route is the active PRIMARY_ACTIVE campaign between seed/resolution changes.

The first actually accepted Child in a route is:

```text
ANCHOR_CHILD
```

Every later accepted Child in the same route is:

```text
CONTINUATION_CHILD
```

Each Child owns its own entry, H1 structural SL, execution record, and PnL.

### ANCHOR

```text
own structural SL -> terminal
same-side H4 Arrivals -> HOLD
CHALLENGE_OPENS -> FULL EXIT
```

### CONTINUATION

```text
own structural SL -> terminal
first subsequent H4-liquidity Arrival -> FULL EXIT
```

This role split naturally produced at most two simultaneous positions in the studied/validated path. `2` is not an independent max-position threshold.

## 8. Entry and execution

Entry is immediate on an eligible tick-native PRIMARY_ACTIVE Arrival; no M1/M5/M15 confirmation pattern is required.

Research execution mapping:

```text
market structure / liquidity chronology: Bid
LONG market entry: Ask-side executable fill
SHORT market entry: Bid-side executable fill
LONG exit economics: Bid-side executable fill
SHORT exit economics: Ask-side executable fill
```

The EA must log semantic reference, requested price, actual fill, spread, and position/deal identity.

Client-side structural guarding and session-close behavior must remain fail-closed and auditable. A failed close is not silently treated as filled; it is retried/logged according to the execution contract.

## 9. No fixed TP

V9 has no fixed TP authority.

Profit-taking comes from semantic Child lifecycle:

- ANCHOR -> CHALLENGE_OPENS
- CONTINUATION -> next H4-liquidity Arrival

Do not add a minimum-R or fixed profit target without a new explicit research program.

## 10. Context that is not an entry veto

`SAME_NEAREST` remains continuation-quality context. It is not a mandatory gate, and `NOT SAME` is not reversal proof.

## 11. Explicit non-rules

No current authority for:

- SHORT prohibition;
- LONG/SHORT balancing;
- session/day/hour filter;
- duration timeout;
- fixed-GOLD SL cap;
- fixed TP;
- cooldown;
- retry count limit;
- trade/day quota;
- fixed no-chase distance;
- AI trade selection;
- LTF confirmation trigger.

## 12. Economic baseline

Primary strategy-validation baseline remains fixed `0.01 lot` actual-tick PnL. R is diagnostic unless a specific equal-money-risk sizing study is being performed.

Risk sizing is a separate portfolio/execution policy and is not part of this prototype authority yet.
