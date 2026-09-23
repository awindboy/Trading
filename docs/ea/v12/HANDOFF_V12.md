# V12 handoff

Last synchronized: `2026-09-23`

## Status

`PHASE 1B JOURNEY CONTRACT FROZEN / IMPLEMENTATION ACTIVE / NO TRADE AUTHORITY`

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

## Completed Phase 0

- The causal raw-M1 pipeline reconstructed every supplied M5 through W1 MT5 bar
  exactly through `2026-09-18 23:57`.
- Two independent builds produced byte-identical output packs.
- The exhaustive universe contains `1,459` C1/C2 records: `1,215` D1->H1 and
  `244` W1->H4. `1,105` have a directional structural hypothesis.
- One dual breach has unresolved same-M1 extreme order and remains ambiguous.
- Phase 0 itself has zero authorized Children, outcomes, or performance records.

## Completed Phase 1A

- The frozen rejection-only prototype produced `1,217` family/risk decisions
  and `426` filled variant records from the Phase-0 universe.
- It compares C3-open control, relative-thick Model #1 confirmation, C2-extreme
  risk, and trigger-structure risk with C1 midpoint as the primary destination.
- Two independent final builds passed complete-pack validation and produced all
  ten files byte-identically. No post-cutoff price row was parsed.
- Full-history Model #1/C2-SL produced `+11.68R`, PF `1.21`, on 156 fills;
  trigger-SL produced only `+2.89R`, PF `1.13`, on 57 fills.
- The recent matched trigger-SL row produced `+8.84R`, PF `2.26`, on only 26
  fills, but retained a `26.92` stopped-unit rate per 100 versus V10's
  `12.52`–`14.07` and was negative in 2022–2023.
- Confirmation removed some losing fills, but its entry delay cost more R.
  Trigger-stop selectivity was recent-window-specific and failed full-history
  stability. Phase 1A therefore does not replace V10.

## What is not yet known

- a reproducible causal true-MSS definition that preserves the source idea
  without discretionary relabeling;
- whether a different predeclared CRT branch can produce a stop population that
  is both lower than V10 and frequent enough to carry meaningful right-tail
  capital;
- whether HA/Wave add incremental information inside CRT states;
- whether any ML head is calibrated and stable across side, year, lane, and
  liquidity era;
- whether the structure survives actual-tick costs and execution constraints.

## Immediate next work

1. implement the frozen H4->M5 shadow CRT journey and causal key-level inventory;
2. map frozen V10 R7G Children and completed FAST flips without changing their
   actions or sizes;
3. separate causal decision context from journey/V10/HA outcomes;
4. report explanation coverage, first/later participation capacity, stop and
   right-tail morphology, and side/year/time stability;
5. independently reproduce the pack before retaining a Phase-1B result.

Do not convert the new journey state into a V10 veto or sizing map during this
phase. Phase 1B tests explanation and lifecycle structure first.
