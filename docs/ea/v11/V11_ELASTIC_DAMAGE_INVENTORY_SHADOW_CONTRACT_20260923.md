# V11 elastic damage-inventory shadow contract

Date frozen: `2026-09-23`

Status: `FUTURE SHADOW ONLY / NO ORDER, RELEASE, SIZING, LEVERAGE, EA, OR PRODUCTION AUTHORITY`

## Purpose

Test whether actual same-run Child damage can temporarily suspend only conviction capital without deleting participation or the persistent-run right tail.

This contract is not a stop predictor. It separates three states of capital:

```text
PARTICIPATION  = one unit for every frozen selected Child
CONVICTION     = two additional units requested by the frozen R7G ceiling
INVENTORY      = HEALTHY or DAMAGED state controlling conviction only
```

## Frozen causal state machine

For each FAST run id independently:

1. Every frozen selected Child receives one participation unit.
2. A selected k1 Child does not receive its two conviction units immediately.
3. If k1 remains alive into the same-direction FAST-k2 decision, the original k1 Hard SL remains valid, and an executable first M1 open exists within 15 minutes, its two conviction units are logged as released.
4. A Child Hard SL known before a later conviction request changes inventory to `DAMAGED`.
5. While `DAMAGED`, every selected Child still receives one participation unit, but its two-unit conviction request is logged as blocked.
6. Inventory returns to `HEALTHY` only when a Child opened after the most recent damage remains alive into a later selected-Child decision in the same FAST run.
7. A new FAST run starts a new inventory state. Cross-run transfer is not authorized by this contract.
8. Existing funded tranches are not closed merely because another Child stops. Damage controls only future conviction requests.
9. Hard SLs remain frozen and are never widened. A stopped Child is never resurrected.

## Same-time and closure handling

- If Hard SL and a conviction request share the same M1 timestamp and exact ticks do not establish order, log both `STOP_FIRST` and `REQUEST_FIRST` shadow outcomes. Do not choose the better result.
- A market-closure or missing-observation release is not moved to a later k. Log `NO_OBSERVATION`.
- `ORDER_FAIL` and `EXIT_PENDING_BLOCK` remain execution diagnostics and do not redefine strategy permission.

## Frozen evaluation population

- market: `GOLD#`;
- evidence after: `2026-09-18 23:57` only;
- comparator: frozen V10 R7G, the complete-portfolio k1 ladder, and this damage-inventory shadow;
- all observations through the freeze timestamp are development evidence and may not be presented as validation.

## Required metrics

- selected Child count and participation retention;
- Hard-SL Child count;
- stopped loss-units and three-unit full stops;
- adjacent full-size stop pairs split into same-run, cross-run, known-prior-stop, and pre-stop-overlap;
- blocked conviction requests, their eventual stop rate, positive/negative R, and L6+ positive-R retention;
- LONG/SHORT and liquidity-era slices;
- funded units, concurrent gross/net units, arithmetic R, cost sensitivity, drawdown, and equal-drawdown capacity;
- all same-M1 ambiguities and market-closure failures.

## Promotion boundary

No threshold or alternate repair duration may be scanned on future observations. Promotion requires enough future blocked requests to assess both directions and more than one liquidity period. Lower stopped units alone is insufficient: blocked non-stops, positive right-tail R, concurrent exposure, and execution feasibility must remain explicit.
