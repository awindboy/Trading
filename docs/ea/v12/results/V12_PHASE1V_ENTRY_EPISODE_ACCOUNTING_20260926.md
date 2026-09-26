# V12 Phase 1V — entry-episode and journey-count result

Status: **complete and byte-reproduced / corrected population confirms negative ordinary drift / primary failed / no action authority**

Date: `2026-09-26`

Interpretation addendum: read `V12_PHASE1W_RETRY_LOCATION_20260926.md` before
using this frozen report. Count curves are not equity; ex-post tail removal
does not prove lack of edge; its tail threshold is weighted Child R>=5; the
48 late-damage cases are a subset of the 338 no-first-stop negatives. Historical
numbers/gates below are retained as originally reported, not universal criteria.

## Why Phase 1U was not the right answer

Phase 1U pooled all selected Children. That mixed three different questions:

1. whether a new journey should be entered;
2. how many additional Children should participate after entry;
3. whether a late Child lost during a pullback or settlement.

It also counted several profitable Children from one large journey as several
independent successes. Phase 1V corrects the grain. One funded FAST run is one
entry episode; its first actual Child represents the start decision, and its
complete episode outcome receives one positive or negative count regardless of
Child count, weight, or R magnitude.

`run_id` remains a FAST-run entry-episode proxy, not proof of the complete larger
market Journey. That limitation is explicit.

## Reconciled population

- funded entry episodes: `679`;
- first actual-entry Children: `679`;
- later Children, reported separately: `730`;
- total original Children: `1,409`;
- missing states, duplicate runs, signal mismatches, decision mismatches, and
  direction mismatches: zero;
- run/Child R, stopped-unit, and tail-unit reconciliation error: below `1e-14`.

Two independent ten-file output packs are byte-identical.

## The real V10 economic shape

| Journey-count proxy | Episodes | Positive | Negative | Tail episodes | Count balance | Net R |
|---|---:|---:|---:|---:|---:|---:|
| All funded episodes | 679 | 197 | 482 | 57 | -285 | +646.18R |
| Non-tail episodes | 622 | 140 | 482 | 0 | -342 | -423.25R |

The actual-R curve is profitable because 57 tail episodes more than offset the
ordinary path. With one equal vote per episode, win rate is only `29.01%` and
the cumulative count curve declines by `285` steps. Excluding tail episodes,
the count slope is `-0.550` per episode and actual R is `-0.680R` per episode.

Between tail episodes there are 53 chronological non-tail blocks. Only seven
are positive and 46 are negative. Median block R is `-5.66R`; mean is
`-7.99R`. This confirms the user's description: the ordinary curve drifts down
and occasional large journeys lift the total curve in steps.

## Entry-only multi-speed result

The frozen policy evaluates FAST/STD/SLOW ownership only at the first actual
entry, then either admits or rejects the complete original episode. It does not
change any later Child.

| Entry accounting | V10 control | Entry ownership policy | Change |
|---|---:|---:|---:|
| Admitted episodes | 679 | 420 | -259 |
| First-Child Hard-SL episodes | 145 | 80 | -65 |
| Repeated first-Child stops | 28 | 12 | -16 |
| Positive episodes | 197 | 127 | -70 |
| Tail episodes | 57 | 41 | -16 |
| Episode win rate | 29.01% | 30.24% | +1.22pp |
| Maximum first-stop streak | 3 | 3 | unchanged |
| Maximum negative-episode streak | 17 | 12 | -5 |
| Non-tail count slope | -0.550 | -0.546 | effectively unchanged |
| Non-tail R per episode | -0.680R | -0.648R | still negative |

First-entry Hard-SL count falls `44.83%` and repeated first-entry stops fall
`57.14%`. But participation falls `38.14%`, positive-episode retention is only
`64.47%`, and tail-episode retention only `71.93%`. Each lost positive episode
buys only `0.93` avoided first stop. The ordinary count slope barely changes.

The policy therefore reduces frequency rather than converting the ordinary
loss process into a positive one. It passes six of ten frozen gates and fails
positive retention, tail retention, stop-to-lost-positive efficiency, and the
positive ordinary-curve gate.

## Which losses are actually entry losses?

The corrected decomposition is decisive:

- first Child Hard SL and negative episode: `144`;
- first Child Hard SL followed by positive recovery: `1`;
- negative episode without a first-Child Hard SL: `338`;
- positive first Child later turned into a negative episode: `48`;
- nonpositive first Child later recovered into a positive episode: `2`.

Thus first-Child Hard SL is a clean bad-start label: `144 / 145` remain negative.
But it explains only `29.9%` of the 482 negative episodes. Another 338 negative
episodes arise without that first stop. The 48 positive-start/late-damage cases
are genuinely post-entry journey-management losses and must not be used to
judge start admission.

First Children carry `297` stopped units and later Children `151`, so entry
quality is the larger stopped-exposure problem. It is still not the whole
ordinary-equity problem.

## What FAST/STD/SLOW can and cannot do here

Confirmed transfer has the lowest first-Child stop rate (`13.78%`) and the least
negative non-tail R per episode (`-0.450R`). It is still not a positive ordinary
process: 62 positive versus 134 negative episodes, with a non-tail count slope
of `-0.497`.

Every one of the five ownership states has a negative non-tail count slope.
Therefore the current multi-speed ownership grammar can rank start risk, but no
state creates the steadily rising ordinary curve sought by the user. Selecting
the best-looking state after observing these outcomes would only tune consumed
data and is prohibited.

## Decision

The user's accounting correction is adopted permanently for this research
question:

- judge admission once per independent entry episode or future true Journey;
- count a large Journey once when evaluating entry hit quality;
- keep later-Child funding and late pullback losses in a separate management
  ledger;
- require the non-tail/count curve to improve, rather than accepting a policy
  because it retains a few oversized tail winners.

Do not promote the Phase-1V ownership gate. The next entry research object must
explain the broader `338` no-first-stop negative episodes and must be defined at
a causal Journey-birth event. Reducing only the 145 clean first-stop failures
cannot turn the ordinary curve upward. No Phase-1V metric, state, or policy has
entry, veto, sizing, trade, EA, or production authority.
