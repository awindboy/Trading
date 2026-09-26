# Phase 1W: failed-seed location, with accounting corrections

Date: 2026-09-26. Consumed development only; no action or sizing authority.

## Scope and reproducibility

V10 comparator research, not a new CRT strategy. The fixed window is
2024-10-01 through 2026-08-28. One first actual entry per funded FAST run:
679 episodes / 1,409 Children. A FAST run is not a proven independent Journey.
Verified raw M1 was streamed again into the original H4 universe (6,770 rows).
Original Child R reconciles within 9e-16. 2021 and later chronology are unopened.
Final packs: `output/v12_phase1w_retry_location_20260926_b` and `_c`.
All eight manifest members are byte-identical. Four focused boundary tests and
the 71-test Phase-1 pattern suite pass. All 379 available reference timestamps
are strictly prior, and no current outcome fields appear in the decision file.

## Corrections to Phase 1U/1V interpretation

These qualifications supersede the earlier interpretation, not frozen outputs:

- The 1,649 selected signals include 1,409 ENTRY, 195 ORDER_FAIL and 45
  EXIT_PENDING_BLOCK. The latter 240 carry hypothetical +94.82713R in the
  selected-signal ledger. +741.01087R therefore is not the same executed-entry
  population as +646.18373R. Neither is a verified monetary MT5 equity result.
- The 57 Phase-1V tail episodes use **Child R times funded units >=5**, not
  unweighted Child R>=5. There are 14 episodes of the latter kind among actual
  entries. Never compare those definitions as though identical.
- A +/-1 count curve measures win frequency, not expectancy or account equity.
  Removing ex-post tail winners is a concentration diagnostic, not proof of no
  edge and not a requirement that a trend strategy profit without its winners.
- Prior curves ordered complete episode outcomes by episode START. They are
  attribution curves, not chronological realized equity or mark-to-market.
- The 48 positive-seed/negative-episode cases are a SUBSET of the 338 negative
  episodes without first-Child Hard SL; they must not be added as disjoint cases.
- Byte-identical reruns establish repeatability, not independent validation.

The prior policy remains failed under its originally frozen gates. Those gates
do not establish a universal need for a positive non-tail count slope, 90% tail
retention, or a particular win rate. No historical output was rewritten.

## Frozen question

At the first entry of an episode, did the immediately preceding episode's first
Child already finish at a loss, and is the new completed H4 close still inside
its signal-H4 range or entry/SL band? Both definitions were fixed before these
cross-tabs. No ML, fitted threshold, new stop, cooldown or post-result tuning.
Prior first-Child exit must be strictly earlier than the new decision. Equal
timestamps remain unavailable; intraminute outcomes are never assumed known.

258 decisions have a known negative prior seed. 300 of all 679 have unavailable
references (including the first row and unresolved/same-time cases). These are
kept, not imputed. Shadow continues to observe original attempts after a mask;
the result is a fixed-book exclusion diagnostic, not a re-executed EA with
retrained feedback or a policy-specific alternate price history.

## Counts and economics

| Metric | Original actual-entry book | H4 footprint exclusion | Risk-band exclusion |
|---|---:|---:|---:|
| Episodes | 679 | 610 | 585 |
| Positive episodes | 197 | 182 | 171 |
| Negative episodes | 482 | 428 | 414 |
| First-Child Hard SL | 145 | 123 | 123 |
| Episode win rate | 29.01% | 29.84% | 29.23% |
| Maximum negative-episode streak | 17 | 17 | 13 |
| Weighted structural R | 646.18 | 634.16 | 627.65 |
| First-seed unweighted R | 104.28 | 97.71 | 95.64 |
| Funded units | 3,305 | 3,044 | 2,925 |
| Stopped units | 448 | 396 | 395 |
| Realized-R drawdown | 57.69 | 52.29 | 49.32 |
| Weighted-tail episodes | 57 | 50 | 50 |
| Unweighted >=5R episodes | 14 | 12 | 12 |

H4 removes 54 negative and 15 positive episodes (3.6 to 1), saving 22 first
Hard SLs. Episode loss rate changes 70.99% -> 70.16%: a modest difference, not
a high-win-rate strategy. It removes 10.16% of attempts and 11.20% of negative
episodes. Weighted R drops 1.86%, while funded units drop 7.90%; this is more
selective than a proportional exposure reduction, but does not prove edge.
Risk-band removes 68 negatives and 26 positives (2.62 to 1); win rate barely
changes. It saves the same 22 first stops with 25 more removed attempts.

No return was rescaled using hindsight stop or drawdown budgets. The drawdown
column groups original Child outcomes at actual recorded exit timestamps with
an initial zero; it excludes floating P/L, commissions, swap and spread changes
not already represented by the source. It is not broker equity or money.

## Stability and mechanism

H4 footprint's removed 69 episodes have 22 first stops (31.88%), versus 123/610
(20.16%) in the retained book. Inside the known-prior-loss cohort, the 69 inside
episodes contain 15 positives; the 179 favorable-outside cases contain 57
positives. These are descriptive associations, not causal treatment effects.
The ten opposed-outside cases are too sparse for a new veto.

H4 weighted R by year, control -> exclusion:

- partial 2024: 52.39 -> 58.06;
- 2025: 389.87 -> 378.94;
- partial 2026: 203.92 -> 197.17.

2025 realized-R drawdown slightly worsens, 42.53 -> 42.80. Risk-band 2025
drawdown worsens more, to 49.32. Both preserve positive pooled LONG and SHORT
R, but baseline SHORT contributes only 7.41R versus LONG's 638.77R. Broad
year/era/future robustness is not established, and 2024 is a short slice.

## Decision and next boundary

There is a modest footprint association, not an oracle and not a resolution of
repeat losses. Do not tune the footprint width, add a best-looking direction
filter, or promote either exclusion. The current exercise does not identify a
true Journey, a destination, or whether a deferred rejected entry can later be
recovered at better terms.

If continued, the distinct question is **delay versus permanent exclusion**:
when a failed-seed footprint is revisited, can a separately frozen price event
create a new independently falsifiable attempt, and what entry-price/SL/cost
penalty does waiting impose? This needs a new chronological event replay with
every rejected and missed episode retained. It must not reuse this result to
tune boundaries or masquerade as an authorized V12 CRT candidate.
