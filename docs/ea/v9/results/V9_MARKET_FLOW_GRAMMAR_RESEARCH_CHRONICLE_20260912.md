# V9 Market Flow Grammar — Research Chronicle

Date: `2026-09-12`
Status: `RESEARCH HISTORY / CURRENT AUTHORITY IS THE CONTINUOUS HIERARCHY DOCUMENT`

## Purpose

This file records how the project arrived at the current grammar, including failed paths and corrections.

It exists so a later session does not repeat discarded research or quote superseded statistics as authority.

---

## Stage 0 — why the grammar project began

The previous V9 workflow repeatedly optimized local trading mechanics:

```text
POI selection
-> M5 trigger
-> entry location
-> trailing / TP
```

Jan-Feb 2026 consumed replay showed:

- H1 candidate opportunities were plentiful;
- the runtime had been under-observing the market by sleeping on distant H4 levels;
- increasing candidate frequency alone did not improve results;
- better LTF entry geometry alone did not repair pitch quality.

This triggered the research pivot:

```text
stop optimizing one trade
-> inspect the continuous answer-sheet flow
-> reverse-engineer a small market grammar first
```

---

## Stage 1 — continuous answer-sheet Atlas proposed

Initial model:

```text
reaction / arrival
-> price delivery
-> next reaction / arrival
-> price delivery
-> ...
```

Research unit changed from `TRADE` to:

```text
FLOW LEG
AUCTION CYCLE
BALANCE / RANGE STATE
DELIVERY PATH
NEXT STATE
```

ICT objects, indicators, session context, and volatility were allowed only as analysis lenses.

Goal:

```text
many flows -> few reusable relationships
```

not:

```text
one explanation per historical move
```

---

## Stage 2 — exact object / arrival Atlas

The existing deterministic object engine was used to preserve exact:

- FVG;
- OB candidate;
- swing/liquidity geometry;
- object lifecycle.

Large consumed object/arrival universes confirmed that the market continuously creates landmarks and that low trade count was not caused by lack of H1 activity.

Important early lesson:

> object existence is not object importance.

---

## Stage 3 — first response / acceptance studies

Early POI/liquidity studies produced apparently strong rejection/acceptance percentages.

Example qualitative idea:

```text
arrival
-> rejection / acceptance
-> next delivery
```

This was useful conceptually, but a later audit found that some of the very high percentages reused part of the classification window inside the measured outcome window.

Correction:

> those early 80-90% figures are answer-sheet descriptive coverage, not clean forward predictive edge.

Do not quote them as strategy performance.

A stricter first-completed-H1-response ledger was built to separate classification time from later movement.
The forward effect was much smaller and more realistic.

---

## Stage 4 — external / popular theory lenses tested

The project deliberately tested plausible auxiliary lenses because raw OHLC alone was unlikely to reveal a useful grammar.

Investigated:

- Asia / London / New York session context;
- London/NY range sweep / reclaim / body break;
- ICT MSS / FVG / breaker / inversion ideas;
- premium / discount;
- MACD;
- Bollinger Bands;
- velocity / occupancy;
- repeated M5 sweeps.

Outcome:

Most generic versions were weak, definition-sensitive, or failed cross-period stability.

Current decision:

- keep them as descriptive vocabulary if useful;
- stop spending active research effort on them;
- do not stack them as confirmations.

One partial idea — recent counterflow liquidity work — showed some contextual value, but not enough to become a fixed sweep-count rule.

---

## Stage 5 — balance hindsight correction

An early answer-sheet study found that the `last accepted probe before the next directional state` matched the next direction around 94% in 2025.

This looked attractive but was methodologically invalid for causal inference because `last before next state` uses knowledge of the future state transition.

A stricter audit tested every balance liquidity arrival.
The result did not preserve the 94% edge.

Final decision:

> the old balance result remains only as correction evidence.

`BALANCE_PROBE_CAUSAL_AUDIT.csv` documents this.

---

## Stage 6 — repair-resumption clue

A small consumed subset suggested:

```text
larger directional H4 state
-> faster H4 repair
-> POI / liquidity arrival
-> first H1 response supports larger state
-> resumed delivery
```

Some small subsets showed 80-90% continuation.

This was useful because it suggested **nested timescales**.

However the sample was too small and the project explicitly rejected optimizing around a rare high-probability setup.

The clue was generalized into a continuous hierarchy instead.

---

## Stage 7 — continuous H4 state machine

Three different causal H4 views were built.

They describe slower authority and faster local direction using different reasonable constructions.

2-of-3 consensus produced:

```text
MIG_UP / MIG_DOWN
PAUSE_UP / PAUSE_DOWN
REPAIR_UP / REPAIR_DOWN
BALANCE
UNRESOLVED_UP / DOWN
AMBIGUOUS
```

The project then compressed the core roles to:

```text
H4 AUTHORITY: STRONG / WEAK / NEUTRAL
H4 PHASE: MIGRATION / LOCAL_INTERRUPT / NEUTRAL
```

PAUSE / REPAIR / UNRESOLVED remain descriptive modifiers, not separate strategy branches.

Strict H4 ledger after boundary correction:

```text
2025 completed bars after warmup: 703
2026 Jan-Feb: 188
```

Macro-state majority covers most time without forcing the rest.

---

## Stage 8 — H1 nested auction discovered at scale

Three causal H1 state views were built and joined only to the latest causally known H4 state.

Inside directional H4 authority, H1 became:

```text
ALIGNED
COUNTERFLOW
LOCAL_BALANCE
```

For the top-level grammar:

```text
COUNTERFLOW + LOCAL_BALANCE -> H1_INTERRUPT
```

Consensus H1 interruption cycles:

```text
2025: 145
2026 Jan-Feb: 41
```

Consensus realignment before H4 side change:

```text
2025: 76.6%
2026: 78.0%
```

This is not a strategy win rate.
It is a repeated nested-timescale topology.

Cross-view 3x3 robustness showed the same topology across different H4/H1 representations.

This shifted the project away from setup mining toward state-process research.

---

## Stage 9 — direction change as a process

Actual directional side changes were connected through their intermediate H4 states.

Strict ledger:

```text
2025: 33 side changes
2026 Jan-Feb: 8
```

Most side changes were not clean `MIG_UP -> MIG_DOWN` vertices.
They commonly passed through:

```text
local interruption
weak authority
neutral / ambiguous buffer
new migration
```

This supported the authority-erosion interpretation.

---

## Stage 10 — confidence becomes market-state information

At H1 interruption start, H4 macro-side agreement mattered strongly.

The important conclusion was not the exact percentage.

It was:

> the same local counterflow has a different semantic role when the slower H4 authority is strong versus internally disputed.

The project therefore stopped trying to eliminate uncertainty with additional indicators.

`STRONG / WEAK / NEUTRAL` became part of the current grammar.

---

## Stage 11 — difficult 2025-05 studied

2025-05 had the lowest consensus H1 realignment among the consumed 2025 months.

Instead of inventing a new filter, the project compared state composition.

May contained:

- less strong H4 authority;
- more weak H4 authority;
- more local-interrupt time;
- more neutral time;
- more actual side changes;
- slower H1-cycle resolution.

Conclusion:

> May is a transition-heavy expression of the same grammar, not a grammar exception.

This is exactly the kind of result the Atlas phase is intended to find.

---

## Stage 12 — ambiguity / unresolved studied

### UNRESOLVED

Directional macro majority exists but exact H4 role is disputed.
It frequently returns to the same migration but has materially higher neutralization risk than clean migration.

It is therefore useful state information.

### AMBIGUOUS

No directional macro majority exists.

2025 consumed episodes:

```text
11 next migrations same as prior side
11 opposite
```

Final decision:

> AMBIGUOUS must remain explicitly non-directional.

Do not search for a tiebreaker simply to remove uncertainty.

---

## Stage 13 — strict boundary correction

A working ledger included a June-source bar whose information-known timestamp was July 1 00:00.

Because July is locked, the final authority uses:

```text
known_at < 2025-07-01 00:00
```

The strict correction changes one headline working count:

```text
H4 migration interruptions
working: 67
final strict: 66
```

All current documents/scripts use `66`.

---

## Current grammar

```text
H4 MACRO AUTHORITY
  STRONG DIRECTIONAL
  WEAK DIRECTIONAL
  NEUTRAL / AMBIGUOUS

-> H4 PHASE
  MIGRATION
  LOCAL_INTERRUPT
  NEUTRAL

-> H1 AUCTION
  ALIGNED
  H1_INTERRUPT

-> EXACT LANDMARKS
  POI / FVG / OB / LIQUIDITY

-> RESOLUTION
  H1 REALIGN
  H4 NEUTRALIZE
  H4 SIDE CHANGE

-> NEXT STATE
```

## Current research priority

Do not reopen generic indicator research.

Next:

1. route / destination after H1 realignment;
2. transit versus campaign-changing landmarks;
3. explicit Same-Parent/Next-Auction versus Parent-Authority-Lost ledger;
4. exact object roles attached to the continuous event ledger;
5. strategy extraction only after those semantics stabilize.

## Permanent mistakes to avoid

- Do not optimize historical high percentages.
- Do not reuse classification-window movement as outcome.
- Do not select `last event before future state` causally.
- Do not make a month-specific rule when state composition explains the month.
- Do not force ambiguous state into direction.
- Do not add indicators to manufacture certainty.
- Do not let one Child result rewrite Parent.
- Do not open July or 2021 early.
- Do not treat answer-sheet Atlas statistics as validation.
