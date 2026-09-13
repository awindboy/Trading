# V9 Arrival / Delivery Grammar and Simple Trading Baseline Checkpoint

Date: `2026-09-13`
Status: `CONSUMED-DATA RESEARCH CHECKPOINT / NOT PRODUCTION AUTHORITY`
Base GitHub HEAD: `ad8bc8efc47cd9478e1b7f7e8d5bfbba398218ce`
Market: `GOLD# ONLY`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`
Consumed answer-sheet blocks: `2025-01..06`, `2026-01..02`
Future-hidden: `2025-07 LOCKED`
Untouched reserve: `2021`

## 1. Why this checkpoint exists

The research intentionally removed most bar-by-bar market-state labels and asked whether V9 can explain price with a small destination-first Grammar.

The resulting research unit is:

```text
MOVING
-> ARRIVAL
-> LIQUIDITY DELIVERY or POI RESPONSE
-> PRIMARY_ACTIVE or CHALLENGED
-> next meaningful liquidity resolution
```

This checkpoint records the evidence obtained before deeper Entry/SL/TP refinement.

## 2. H4 arrival stream

The consumed H4-arrival stream contained approximately:

```text
all grouped H4 arrival times: 408
UP:                       192
DOWN:                     207
OVERLAP / ambiguous:        9
```

Research split:

```text
H4-liquidity delivery arrival times: about 185
POI-only arrival times:              about 223
```

The main lesson was not the count itself. It was that raw UP/DOWN arrival color flips are too frequent to equal route flips.

## 3. Liquidity vs POI role separation

Descriptive audits showed:

- H4-liquidity arrival was strongly associated with extension/progression of the same-side delivery structure;
- POI-only arrival was much less consistently associated with such progression;
- individual POI touch/orientation did not provide a stable continuation/reversal classifier;
- POI interactions frequently occurred inside routes that later continued in the same delivery direction.

Research interpretation:

```text
LIQ -> delivery/progression evidence
POI -> response/interaction evidence
```

This is semantic role separation, not a rule that every liquidity event is external/major or every POI is minor.

## 4. Compact LIQ resolver

Consumed study used the following threshold-free resolver:

```text
PRIMARY_ACTIVE(A)
  opposite H4 LIQ B -> CHALLENGED(A,B)

CHALLENGED(A,B)
  next H4 LIQ A -> PRIMARY_CONTINUES(A)
  next H4 LIQ B -> CHALLENGER_EARNED(B)
```

Observed opposite-liquidity challenge resolutions:

```text
challenge episodes:       39
OLD_ROUTE_CONTINUES:       17
CHALLENGER_EARNED:         22
```

Against the provisional answer-sheet route interpretation used only as a research comparator:

- most `CHALLENGER_EARNED` resolutions aligned with the manually reconstructed new route;
- most `OLD_ROUTE_CONTINUES` resolutions aligned with old-route persistence;
- a small number of conflicts remained, concentrated in a few difficult episodes;
- H4/H1 context did not supply a clean rule that removed only those errors without harming correct cases.

Research decision: do not add exception rules merely to eliminate the residual mismatches.

## 5. Explicit uncertainty audit

When `CHALLENGED` hours were not forced into a direction, the remaining `PRIMARY_ACTIVE` hours aligned much more closely with provisional manual route direction.

Approximate descriptive comparison:

```text
2025H1:
  PRIMARY_ACTIVE coverage of manual-route hours ~80%
  direction agreement while ACTIVE            ~93%

2026 Jan-Feb:
  PRIMARY_ACTIVE coverage                      ~74%
  direction agreement while ACTIVE             ~88%
```

These are representation-agreement figures, not predictive accuracy.

Important consequence:

```text
CHALLENGED / UNRESOLVED is useful information.
Coverage does not need to be 100%.
```

## 6. Structural continuation tendency

Within `PRIMARY_ACTIVE`, consumed H4-liquidity delivery-to-next-liquidity windows showed:

```text
same-side next H4 LIQ: 105 / 144 ~= 72.9%
opposite-side next LIQ: 39 / 144 ~= 27.1%
```

Approximate stability checks:

```text
2025H1        ~72.5%
2026 Jan-Feb  ~74.3%
UP            ~71.7%
DOWN          ~75.0%
```

Monthly results varied materially, so this is an edge candidate under uncertainty, not a law.

After `CHALLENGER_EARNED`:

```text
next H4 LIQ same side: 18 / 22 ~= 81.8%
```

This subset is promising but small.

## 7. POI response audit

A simple POI-only next-liquidity analysis did not earn a direction rule.

Examples from consumed research:

- pullback into a primary-supporting POI did not produce a sufficiently stable next-direction result by itself;
- primary-forward arrival into an opposing POI was near coin-flip in the tested sample;
- POI structure inside `CHALLENGED` did not reliably identify the eventual resolver winner;
- same-time opposing POI interaction could still occur during strong same-side liquidity progression.

Therefore no POI-based reversal/continuation gate was frozen.

## 8. Time audit

Delivery-to-next-liquidity and POI-to-next-liquidity timing distributions overlapped heavily between continuation and challenge outcomes.

Although median times differed descriptively, no causal timeout/cooldown/duration threshold was earned.

Do not create one from this checkpoint.

## 9. Dynamic destination audit

The H4 swing-liquidity candidate reconstruction reproduced `220/220` strict H4 liquidity object IDs used in the consumed audit.

Across `122` same-primary continuation pairs:

```text
next actual target already known at current delivery: 61
next actual target born after current delivery:        61
```

There were `31` cases where no known active same-side H4 liquidity destination remained immediately after the current delivery, yet same-primary delivery later continued after new liquidity formed.

In that exploratory subset, new target birth occurred roughly `35h` after the prior delivery at the median.

Conclusion:

```text
ACTIVE_DESTINATION_SET is dynamic.
Destination rollover is normal.
A route cannot be defined by one fixed final target.
```

## 10. Deliberately simple trading baseline

Purpose:

```text
not to optimize V9;
only to verify that the simplified semantic edge can be translated into bounded-risk attempts.
```

Prototype family:

```text
STATE
  PRIMARY_ACTIVE

ENTRY
  descriptive next-H1-open comparator after causal active H4-liquidity delivery confirmation

TP
  nearest causally known same-side H4 liquidity destination

HARD SL COMPARATORS
  signal H1 extreme
  nearest opposite H1 structural swing
  nearest opposite H4 structural swing

POSITION COMPARATOR
  one-position-at-a-time variant also tested
```

No minimum-R filter was used.

### Qualitative SL result

```text
signal-H1 extreme
-> narrow
-> attractive nominal reward/risk
-> too many normal-journey stops

H4 structural swing
-> wide
-> high hit rate
-> weak R efficiency

H1 structural swing
-> best simple balance in this first study
```

### Exploratory performance scale

The interactive prototype reported roughly:

```text
H1 structural SL + one-position comparator
resolved win rate ~70%
net ~+8R
max drawdown ~4.4R
```

A nearby independent local reconstruction against the authoritative M1 hash, using slightly different still-unfrozen warm-up/execution details, produced a similar resolved win rate and roughly `+9R`.

The exact value is therefore intentionally **not frozen**.

### CHALLENGER_EARNED subset

The small subset was stronger in the prototype:

```text
roughly 75-79% resolved wins
roughly +5.6R to +6.6R depending on still-unfrozen convention
```

This is only a prioritization clue for the next research contract.

## 11. SL / TP scale observed in the simple baseline

The H1-structural-SL comparator showed a typical scale where Hard SL was often wider than the nearest known liquidity TP.

Interactive prototype median scale was approximately:

```text
Hard SL distance: ~40 GOLD price units
TP distance:      ~25 GOLD price units
TP / SL:          ~0.6R median
```

This is an important qualitative finding:

```text
V9 may be a higher-hit-rate destination-to-destination process,
not automatically a 1:3 / 1:5 fixed-R system.
```

Do not turn the median into a minimum/maximum distance rule.

## 12. What is and is not frozen

Frozen as current semantic research direction:

- MOVING / ARRIVAL simplification;
- liquidity as delivery/progression evidence;
- POI as response/interaction evidence;
- PRIMARY_ACTIVE / CHALLENGED / PRIMARY_CONTINUES / CHALLENGER_EARNED vocabulary;
- explicit uncertainty;
- dynamic destination-set interpretation;
- no hidden threshold additions.

Not frozen:

- exact Entry rule;
- exact Hard-SL selector;
- exact TP/journey rule;
- one-position vs overlapping Child policy;
- automatic action on CHALLENGED for an already-open Child;
- exact performance figures;
- spread/slippage/tick execution convention for this baseline;
- production/live route initialization.

## 13. Data safety

No future-hidden July or final-reserve 2021 data was intentionally opened for this research checkpoint.

```text
2025-07 = LOCKED
2021    = UNTOUCHED FINAL RESERVE
```
