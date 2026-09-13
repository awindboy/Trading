# V9 Next Research Contract — Arrival/Delivery Trading Refinement

Date: `2026-09-13`
Status: `ACTIVE NEXT RESEARCH CONTRACT`
Production authority: `NONE`
EA authority: `NONE`
Market: `GOLD# ONLY`
Future-hidden: `2025-07 LOCKED`
Untouched reserve: `2021`

## 1. Objective

The project has completed enough market-state simplification to stop expanding the taxonomy and begin serious trading extraction.

The next objective is:

> turn the compact `PRIMARY_ACTIVE / CHALLENGED` arrival-delivery Grammar into the simplest causal Child process that has positive expectancy under uncertainty, without hindsight repair or hidden thresholds.

Do not attempt to explain every residual mismatch before proceeding.

## 2. Fixed semantic starting point

Use:

```text
MOVING
ARRIVAL

ARRIVAL ROLE
  H4 LIQ -> DELIVERY / PROGRESSION
  H4 POI -> RESPONSE / INTERACTION

ROUTE STATUS
  PRIMARY_ACTIVE
  CHALLENGED / UNRESOLVED
  PRIMARY_CONTINUES
  CHALLENGER_EARNED
```

Do not reintroduce STRONG/WEAK/ALIGN/INTERRUPT/REALIGN as top-level trading states.

## 3. Workstream A — freeze the baseline before optimizing it

Create a versioned script and result ledger that reproduce the simple baseline from raw/approved consumed inputs.

Freeze explicitly:

```text
source files + hashes
consumed byte/date ranges
object warm-up policy
OBJECT_KNOWN_AT convention
H4-liquidity event grouping convention
PRIMARY initialization convention
entry authorization time
entry price reference
Hard-SL object selection
TP object selection
spread / Bid-Ask convention
M1/tick touch ordering
same-M1 SL/TP ambiguity handling
position overlap comparator
censoring rules
R and point arithmetic
```

Acceptance:

- repeated runs byte-identical;
- no future-hidden rows revealed;
- exact result ledger and summary hash stored;
- exploratory session figures may change slightly after convention freeze; the frozen script wins.

## 4. Workstream B — entry-context decomposition

Compare the same basic structural Entry/SL/TP family under these causal semantic events:

```text
PRIMARY_DELIVERY
PRIMARY_CONTINUES
CHALLENGER_EARNED
```

Do not add a minimum-R filter.

Questions:

- is `CHALLENGER_EARNED` genuinely a higher-quality first Child opportunity or only small-sample luck?
- is repeated `PRIMARY_DELIVERY` later in an established journey lower quality because the nearest remaining destination is too close?
- does `PRIMARY_CONTINUES` after a failed challenge produce a different payoff distribution?

Required outputs:

```text
trade count
win/loss/censored/ambiguous
R distribution
price-point distribution
SL-distance distribution
TP-distance distribution
TP/SL distribution
MAE/MFE where causal execution allows
max drawdown
route-level concentration
block/month/side stability
```

Statistics are descriptive evidence, not automatic thresholds.

## 5. Workstream C — structural Entry geometry

Within `PRIMARY_ACTIVE`, study whether waiting for a counter-move / response interaction improves the Child without destroying opportunity.

Candidate factual contexts may include:

```text
counter-move into primary-supporting H1/H4 structure
POI response after a primary liquidity delivery
revisit of a code-owned structural reference
fresh trigger formation on M15/M5 only after HTF authorization
```

Do not assume POI touch itself is directional edge. The study must ask whether a causal trigger creates a better entry price / tighter valid Hard SL while preserving the larger delivery thesis.

No fixed retracement percentage, candle count, elapsed-time limit, or no-chase distance may be invented unless separately earned.

## 6. Workstream D — Hard SL refinement

Hard SL remains fixed before entry and never widened.

Use the simple study as comparator:

```text
signal H1 extreme -> often too tight
H1 structural swing -> current best simple comparator
H4 structural swing -> often too wide
```

Research alternatives must be structural and causal, for example:

- exact response-origin structure;
- code-owned POI distal invalidation where semantically justified;
- local swing invalidation tied to the actual Child thesis;
- trigger-scale structure after HTF authorization.

Do not optimize SL solely to maximize historical R.

For every SL candidate report:

```text
why this price invalidates the Child thesis
how often ordinary route noise reaches it
loss size distribution
win size distribution
impact on expectancy and drawdown
```

## 7. Workstream E — TP / journey refinement

Current simple comparator:

```text
nearest causally known same-side H4 liquidity
```

But destination research proved that the active destination set is dynamic.

Therefore compare:

```text
A. fixed nearest-known destination at entry
B. destination rollover / journey management when new same-side destinations become known
C. partial or semantic review at arrival while preserving a fixed Hard SL
```

Do not backdate a newly born destination into the original trade plan.

If a destination was unknown at entry, it may influence only decisions made after its causal known-at time.

No fixed TP multiple may be inserted by default.

## 8. Workstream F — CHALLENGED while a Child is open

For new-entry research:

```text
CHALLENGED = NO NEW DIRECTIONAL EDGE ASSUMED
```

For an already-open Child, do **not** assume automatic exit.

Compare causally:

```text
Hard-SL-only hold
semantic review at challenge
partial/exit/remap only if an explicit rule is frozen
```

Stopped Child is always dead.

The study must distinguish:

```text
Parent/route semantic uncertainty
vs
Child thesis invalidation
```

## 9. Workstream G — repeated Child attempts / exposure

One-position-at-a-time was only a comparator, not final authority.

Study:

- overlapping Children in one primary journey;
- repeated attempts after a completed Child;
- route-level cumulative risk;
- whether multiple entries are genuinely independent or just duplicated exposure.

Do not create a retry cap, cooldown, trade/day quota, or forced spacing rule from convenience.

If exposure control becomes necessary, derive it explicitly from portfolio/risk reasoning and document it separately from market edge.

## 10. Workstream H — AI role after mechanical baseline

Do not call AI simply to reproduce facts that code can own.

Potential AI role only after mechanical baseline is frozen:

```text
semantic quality of origin / response / destination role
selection among multiple valid structural Child invalidation references
journey interpretation at meaningful arrival/review events
handling genuinely unresolved competing routes
```

Compare:

```text
mechanical baseline
vs
AI-assisted semantic selection
```

on consumed data before any hidden replay.

## 11. Required counterexample policy

Residual failures do not automatically justify new rules.

For any proposed filter/exception:

1. identify the causal fact available at the time;
2. show it across all consumed occurrences, not only the motivating loss;
3. report what correct trades it removes or changes;
4. reject it if it merely fixes one or two historical episodes;
5. preserve `UNRESOLVED / NO-EDGE` when no clean distinction exists.

## 12. Hidden-data gate

Do not open `2025-07` or `2021` during this contract.

Before July can even be reconsidered, all of the following must be true:

```text
- semantic authority frozen
- simple baseline reproduction frozen
- chosen Entry/SL/TP/journey policy preregistered
- deterministic runtime implementation updated for the new Grammar
- consumed replay parity passed
- exact hashes committed
- no open implementation/parity gate
- position state FLAT or explicitly checkpointed per protocol
```

Until then:

```text
2025-07 = LOCKED
2021    = UNTOUCHED
```

## 13. Success criterion

Success is not a perfect classifier and not a target win rate.

Success is:

> a compact causal policy that makes good bounded-risk attempts when `PRIMARY_ACTIVE` is understandable, explicitly stands aside when the route is unresolved, and lets rare wrong interpretations die through precommitted Hard SL rather than hindsight repair.
