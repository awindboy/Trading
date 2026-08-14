# Mentor Protocol V2.1: HTF Root Amendment

## Why this amendment exists

The June 9-10 calibration replay exposed a protocol mismatch:

- The only trade whose source was a predeclared M15 OB reached its objective.
- Three later trades promoted a standalone M5 displacement OB to the scenario root.
- That promotion does not reproduce the mentor's repeated workflow of locating a
  higher-timeframe OB first and then reducing the stop through lower-timeframe
  refinement.

Those three losses are not classified as market uncertainty. They are protocol
violations because the scenario did not have a valid HTF root cause.

## Frozen source hierarchy

1. The root source must be a pre-existing OB on H1, M30, or M15.
2. M5 may refine that root only when it overlaps the parent price event and its
   displacement explains the same structural delivery.
3. M5 cannot independently authorize a first position.
4. M1 is trigger-only:
   parent/refined source touch -> pre-existing liquidity sweep -> separate
   body-close CHoCH -> CHoCH-owned FVG or OB -> later retest.
5. A CHoCH-owned M1 FVG remains a valid first-entry execution zone. This
   amendment does not force entry at the parent OB boundary.
6. Continuation FVG add-ons remain out of scope until the first-entry protocol
   has positive blind evidence.

## Loss classification

`MARKET_UNCERTAINTY` is allowed only when the order has:

- a predeclared H1/M30/M15 root OB,
- a valid optional M5 causal refinement,
- a fresh liquidity sweep inside that context,
- a separate M1 CHoCH,
- a CHoCH-owned execution zone and later retest,
- structural SL and exact frozen objective liquidity.

Missing the HTF root is a scenario-construction error, regardless of PnL.
