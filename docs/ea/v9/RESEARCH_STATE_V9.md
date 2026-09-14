# V9 Research State

Date: `2026-09-14`
Status: `PROTOTYPE COMPLETE / ACTUAL-TICK VALIDATION COMPLETE / LIVE-RISK POLICY UNFROZEN`
Market: `GOLD# ONLY`

## Current thesis

V9 no longer depends on predicting every destination. The active mechanical thesis is:

```text
Arrival / Delivery Grammar
+ H1 structural invalidation
+ long-era volatility normalization (H4 ATR180)
+ role-separated Children
+ tick-native execution
```

## Prototype performance hierarchy

### M1 research prototype

ERA4 + role-based management showed strong fixed-size gross performance and bounded natural overlap.

### Actual MT5 real ticks

Actual execution materially reduced the M1 result but did not erase the aggregate edge.

```text
2022 through 2026-08-28
1,316 closed
+5,028.62
PF 1.425
WR 60.18%

full uploaded closed ledger through 2026-09-09
1,322 closed
+4,954.61
PF 1.412
WR 60.14%
```

By direction across the full closed ledger:

```text
UP    731 trades / +4,836.20 / PF 1.832
DOWN  591 trades /   +118.41 / PF 1.019
```

By role:

```text
ANCHOR        355 / +2,439.43 / PF 1.498 / WR 37.2%
CONTINUATION  967 / +2,515.18 / PF 1.353 / WR 68.6%
```

This supports the intended role split: Anchor preserves the right tail; Continuation harvests local delivery.

## Exit evidence

```text
CHALLENGE_OPENS                  232 / +5,529.48 / PF 4.06
NEXT_H4_LIQ                     761 / +7,901.62 / PF 5.56
STRUCTURAL_SL                   255 / -6,324.70
TICK_COLLISION_STOP_CHALLENGE    30 /   -978.86
TICK_COLLISION_STOP_NEXT_LIQ     44 / -1,172.93
```

There is no fixed TP. Semantic exits are part of the Grammar/Child-role contract.

## Structural-risk evidence

Actual-entry-to-Hard-SL distance over 1,322 closed trades:

```text
median 22.56 GOLD
P75    36.97
P90    65.44
P95    91.72
P99   164.19
max   225.65
```

After ERA4 eligibility, wide absolute stops are not automatically poor trades. In the actual-tick ledger, the 3-4 ATR180 bucket remained strongly positive. Do not reintroduce a fixed-GOLD stop cap.

## Time slices are descriptive, not rules

All weekdays and all four broad source-time session buckets were gross-positive, but substantial hour/day/direction interactions exist. No session, weekday, hour, or duration filter is current authority.

Long-held surviving Anchors create a large right tail; negative 4h-3d cohorts contain survivorship/path-selection effects and must not become a duration timeout.

## Money management

Fixed 0.01 lot remains the primary validation comparator.

Canonical sizing research:

- 1% target on full history from $1,000: end `$5,876.54`, max balance DD `36.77%`, minimum-lot oversize on `80.66%` of entries.
- 2025+ risk grid shows rapidly rising drawdown above 3-5% Child risk.
- 10% per Child from $1,000: end `$21,172.22`, marked equity `$21,852.95`, peak `$106,529.39`, max balance DD `85.47%`, max lot `2.76`.

These are sizing experiments, not production recommendations.

## Open research risks

- SHORT expectancy is marginal under actual ticks.
- session-close/reopen gaps can materially worsen fills.
- client-side structural SL requires robust restart/disconnect handling.
- large-lot replay assumes linear fills and ignores size-dependent market impact/margin constraints.
- current actual-tick forward-like post-2026-08-28 sample is too small for statistical conclusions.
