# V12 handoff

Last synchronized: `2026-09-23`

## Status

`ACTIVE ARCHITECTURE AND EVENT-DEFINITION RESEARCH / NO TRADE AUTHORITY`

V12 begins because V10/V11 did not selectively remove enough stopped Children.
The new base is CRT journey structure, not a FAST-HA ledger with another veto.

## Current assembly

- Candidate generator: causal CRT C1/C2 state and confirmed C3 Child.
- Official lanes: W1 -> H4 and D1 -> H1.
- Secondary observations: FAST/STD/SLOW HA, Wave Candle coordinates, normalized
  sweep/settlement/liquidity measurements, SMT only after paired-symbol data are
  verified.
- ML: shadow-only competing-outcome and conditional-R estimation.
- Research oracle: verified chronological raw M1.
- Implementation gate: Python/MQL5 event-ledger parity before tester economics.

## What is not yet known

- the smallest reproducible numeric definition of Model #1 and true MSS that
  preserves the source idea without discretionary relabeling;
- whether CRT candidates have a materially different stop population from V10;
- whether HA/Wave add incremental information inside CRT states;
- whether any ML head is calibrated and stable across side, year, lane, and
  liquidity era;
- whether the structure survives actual-tick costs and execution constraints.

## Immediate next work

1. build a causal C1/C2 event universe for W1->H4 and D1->H1;
2. audit candidate labels manually without outcomes visible;
3. freeze two structural Hard-SL variants and the C1 50%/opposite-extreme targets;
4. produce the first no-ML baseline scorecard;
5. add HA/Wave coordinates only after the base ledger is stable;
6. add ML only after features have causal and MQL5 parity specifications.

Do not build an optimization EA first. The first deliverable is a trustworthy
numeric event ledger with explicit ambiguous and rejected states.
