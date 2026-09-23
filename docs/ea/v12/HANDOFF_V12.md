# V12 handoff

Last synchronized: `2026-09-23`

## Status

`PHASE 1B COMPLETE AND REPRODUCIBLE / TRANSITION DIAGNOSTIC ONLY / NO TRADE AUTHORITY`

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

## Completed Phase 1B

- Raw M1 produced `7,287` exhaustive H4 pairs, `4,819` activations, `2,649`
  canonical journeys, `17,610` key levels, and `2,234` FAST flips.
- Two independent packs passed complete validation and were byte-identical;
  zero post-cutoff price rows were parsed.
- All `1,649` selected R7G Children remained unchanged at `3,881` units,
  `486` stopped units, and `+741.010865R`.
- Aligned journey Children had `10.43` stopped units per 100 funded versus
  `20.79` when opposed, but opposed Children retained `+195.72R`; relation is
  not a veto.
- After a FAST flip, opposite CRT authorization had a `26.12%` linked-k1 stop
  rate versus `36.93%` without authorization. The lower stop rate held in every
  consumed year. The non-authorized group still earned `+35.42R`, so this is
  transition-risk evidence, not permanent rejection authority.
- A key arrival by itself did not resolve whether the flip was counterflow or a
  new journey.

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

1. freeze a future-only transition shadow around `authorize opposite / neutral
   bridge / later reauthorize`, without treating non-authorization as rejection;
2. test FAST/STD/SLOW and Wave only conditionally inside the five Phase-1B flip
   states;
3. keep immediate new-direction stop, later repair, and right-tail continuation
   as separate outcomes;
4. test first/later aligned status as conviction information without a fixed
   capital ladder;
5. preserve GOLD# 2021 and post-cutoff chronology until the next contract is
   frozen.
