# V9 Research State

Date: `2026-09-13`
Status: `ACTIVE / ARRIVAL-DELIVERY GRAMMAR / SIMPLE BASELINE COMPLETE / REFINEMENT NEXT`
Production authority: `NONE`
EA authority: `NONE`
Market: `GOLD# ONLY`

## Current research thesis

The useful V9 hypothesis has become simpler:

```text
price spends most of its time MOVING between meaningful arrivals;
meaningful ARRIVAL events reveal delivery/progression or response/interaction;
route uncertainty does not need to be forced into a direction;
trading edge should be extracted only where the semantic state is clear enough.
```

The project no longer aims to classify every local price fluctuation.

## Current compact Grammar

### Top-level

```text
MOVING
ARRIVAL
```

### Arrival attributes

```text
SIDE
  UP / DOWN / OVERLAP-UNRESOLVED

ROLE
  H4 LIQUIDITY -> DELIVERY / PROGRESSION
  H4 FVG / OB  -> RESPONSE / INTERACTION
```

### Slow route status

```text
PRIMARY_ACTIVE(side)
CHALLENGED / UNRESOLVED
PRIMARY_CONTINUES
CHALLENGER_EARNED
```

Candidate causal resolver:

```text
opposite H4 LIQ arrival opens CHALLENGED;
next H4 LIQ old-side -> PRIMARY_CONTINUES;
next H4 LIQ challenger-side -> CHALLENGER_EARNED.
```

This resolver has no fixed time/count/R/ATR rule.

## What has been retired from the top-level model

These remain contextual or historical only:

- STRONG / WEAK / alignment state as the Grammar itself;
- H1 interrupt / realign as automatic route changes;
- 9-state / 8-transition policy tables;
- FLOW_ROUTE boundaries forced from H1/H4 state-run boundaries;
- POI touch as automatic route-completion or reversal evidence.

H4/H1 labels remain useful observations inside a route.

## Current consumed evidence

Primary evidence sources:

```text
docs/ea/v9/results/market_flow_atlas/MARKET_FLOW_EVENT_LEDGER.csv
docs/ea/v9/results/market_flow_atlas/POI_INTERACTION_CLUSTER_STUDY_STRICT.csv
docs/ea/v9/results/market_flow_atlas/LIQUIDITY_DELIVERY_CLUSTER_STUDY_STRICT.csv
docs/ea/v9/results/market_flow_atlas/CONTINUOUS_H1_NESTED_STATE_LEDGER.csv
scripts/v9_ict_object_engine.py
```

Latest findings:

1. `PRIMARY_ACTIVE` H4-liquidity delivery -> next H4 liquidity same side was about `72.9%` across `144` active delivery windows.
2. The two consumed blocks were similar (`~72.5%` and `~74.3%`), and UP/DOWN were also similar overall, but monthly results varied materially.
3. `CHALLENGER_EARNED` -> next H4 liquidity same side was about `81.8%` in only `22` consumed events. This is promising but small-sample.
4. POI orientation/touch alone did not provide a stable next-direction edge.
5. POI activity inside `CHALLENGED` did not reliably resolve uncertainty.
6. Delivery-to-next-delivery time distributions overlapped heavily; no timeout was earned.
7. Explicit unresolved state is useful: difficult periods become `CHALLENGED` rather than requiring special labels.

These are structural event statistics, not trade win rates.

## Dynamic destination result

The consumed H4 swing-liquidity reconstruction reproduced all `220` strict H4 liquidity object IDs used in the audit.

For `122` same-primary continuation pairs:

```text
next actual same-side target already known at current delivery: 61
next actual same-side target born only after current delivery:   61
```

There were `31` continuation pairs where no known active same-side H4 liquidity destination remained immediately after the current delivery, yet the route later continued after new liquidity formed. In that subset, new target birth occurred roughly `35h` after the prior delivery at the median in the exploratory audit.

Interpretation:

```text
ACTIVE_DESTINATION_SET must be dynamic.
A route is not one fixed destination.
Current destination exhaustion alone cannot close a route.
```

## Simple trading baseline completed

The project has now done enough deliberately simple trading work to justify moving into refinement.

Baseline family:

```text
PRIMARY_ACTIVE
-> causal H4-liquidity delivery confirmed on H1
-> enter at next H1 open comparator
-> TP nearest known same-side H4 liquidity
-> structural Hard SL comparator
```

SL comparison qualitatively showed:

```text
signal-H1 extreme -> too tight / too many normal-noise stops
H4 swing          -> too wide / high hit rate but weak R efficiency
H1 swing          -> best simple balance in this preliminary study
```

The H1-swing one-position exploratory result was around `70%` resolved win rate and roughly `+8R to +9R` in the consumed study, with maximum drawdown around `4.4R` in the tested comparator.

The `CHALLENGER_EARNED` subset was stronger but small, around `75-79%` resolved wins.

Exact P&L is **not frozen** because the baseline reproduction script, warm-up/object availability convention, spread/tick convention, and all execution details have not yet been committed as one versioned study.

No minimum-R rule or performance target was adopted.

## Current primary unknowns

The highest-value unknowns are now trading-policy questions inside the simplified Grammar:

1. what is the cleanest causal entry geometry inside `PRIMARY_ACTIVE`;
2. whether `PRIMARY_DELIVERY`, `PRIMARY_CONTINUES`, and `CHALLENGER_EARNED` deserve different entry handling;
3. where the structurally correct Child Hard SL belongs without becoming unnecessarily wide;
4. how to use dynamic destinations for TP/journey management;
5. whether and how repeated Child attempts inside one primary journey add edge without hindsight or hidden retry caps;
6. how an already-open Child should behave when `PRIMARY_ACTIVE` becomes `CHALLENGED`;
7. whether the preliminary `CHALLENGER_EARNED` advantage survives a frozen reproduction and larger consumed review;
8. whether AI adds value beyond the simple semantic resolver once the mechanical baseline is frozen.

## Immediate outputs to build next

```text
versioned simple-baseline reproduction script
simple-baseline exact result ledger
entry-context comparison: PRIMARY_DELIVERY vs PRIMARY_CONTINUES vs CHALLENGER_EARNED
structural Hard-SL audit
journey / destination-management audit
open-Child-under-CHALLENGED audit
unresolved / no-edge case ledger
```

Do not add a new state merely to improve coverage.

## Data classification

```text
2024         consumed postmortem/research
2025 Jan-Jun consumed answer-sheet
2026 Jan-Feb consumed answer-sheet
2025-07      future-hidden LOCKED
2021         untouched final reserve
```

Future-hidden gate: `NOT SATISFIED`.
