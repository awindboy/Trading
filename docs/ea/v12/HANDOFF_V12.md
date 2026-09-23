# V12 handoff

Last synchronized: `2026-09-24`

## Status

`PHASE 1D COMPLETE AND REPRODUCIBLE / TIME IS STATE, NOT VETO / NO TRADE AUTHORITY`

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

## Completed Phase 1C

- The frozen Parent-clock experiment found `118` selected Children across `60`
  old-journey bridge episodes; `31` episodes repaired to the original FAST
  direction before Parent termination.
- Broad active-Parent carry changed all 118 Children and raised R from
  `+741.01R` to `+764.20R`, but stops rose from `232` to `258`, stopped units
  from `486` to `552`, funded unit-hours by `5.6%`, and grouped realized DD from
  `57.00R` to `62.49R`.
- Its best bridge supplied `+36.94R`; without that one episode broad carry was
  `-13.75R` versus baseline. It is rejected as a holding rule.
- Requiring the origin C1 opposite edge to remain unresolved changed only 12
  Children. It added `+17.01R` with slightly better PF/DD, but the best episode
  supplied `85.8%` of the gain and 2025 was negative versus baseline.
- The 31 repair Children added only `+0.42R` versus their ordinary k1 exit clock;
  26 were already selected by R7G. One added repair unit improved basket average
  entry in only `5 / 31` cases.
- Two complete packs were byte-identical and parsed zero post-cutoff price rows.

## Completed Phase 1D

- MT5 exported `68,377` economic-calendar values; eight conflicting duplicate
  IDs were excluded. `20,271` timed release clusters remained.
- Broker hour `16` ranked first in normalized daily activity in 2022–2025 and
  second in 2026, but its V10 capital retained `+203.53R`; fixed-hour avoidance
  is rejected.
- USD-high releases added median 15-minute tick/range lift of `1.11x/1.15x`
  versus eight matched prior weeks, decaying toward baseline by four hours.
- The joint state `hour 20 + aligned journey + USD moderate/high release in
  30–60 minutes` had 35 Children, `24.73` stopped units per 100, and `-13.85R`
  versus `3.85` stopped units and `+3.62R` for other matched hour-20 aligned
  Children. The 35-event cell is shadow-only.
- After a USD moderate/high release, larger causal surprise magnitude coincided
  with shorter FAST runs and higher linked-k1 stop rates (`16.28%` to `27.11%`).
  It informs flip meaning; it is not a news-direction or admission rule.
- Two independent builds were byte-identical and parsed zero post-cutoff price
  rows.

## What is not yet known

- a reproducible causal true-MSS definition that preserves the source idea
  without discretionary relabeling;
- whether a different predeclared CRT branch can produce a stop population that
  is both lower than V10 and frequent enough to carry meaningful right-tail
  capital;
- whether HA/Wave add incremental information inside CRT states;
- how to maintain a causal rolling target inventory after C1 midpoint and
  opposite edge are consumed without inventing a hindsight key-level score;
- whether any ML head is calibrated and stable across side, year, lane, and
  liquidity era;
- whether the structure survives actual-tick costs and execution constraints.

## Immediate next work

1. freeze a target-first Parent inventory using the existing causal one-use
   H4/day/week/month levels, with deterministic succession and no family score;
2. distinguish `unfinished target`, `target complete / reframe pending`, and
   actual Parent invalidation before retesting carry;
3. retain the Phase-1C repair definition but do not add capital until the target
   state exists and future evidence accumulates;
4. carry the two frozen Phase-1D temporal interactions as shadow fields inside
   the target-state work; do not turn them into hour/news vetoes;
5. test FAST/STD/SLOW and Wave only conditionally inside the frozen CRT states;
6. preserve GOLD# 2021 and do not reinterpret the still-unread post-cutoff
   chronology after its shadow semantics are frozen.
