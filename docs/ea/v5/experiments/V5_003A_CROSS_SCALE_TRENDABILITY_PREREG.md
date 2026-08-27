# V5-003A — Cross-Scale Trendability Context Pre-registration

Status: `PRE-REGISTERED BEFORE V5-003A OUTCOME ANALYSIS`
Freeze date: `2026-08-27`
Parent result: `V5-002 balance-generated directional mechanism NOT SUPPORTED`
Strategy authority: `NONE`

## Motivation

V5-002 found:
- event-scale balance descriptors did not stably explain breakout direction;
- expansion/trendiness did stably explain later movement intensity;
- non-causal whole-week aggregation suggested slow regime variation, but that aggregation cannot be used as a feature.

Successful-trader/source regression suggests a new, separate question:
technical continuation patterns may matter only when interpreted inside a stronger higher-timeframe trendability state.

This is NOT a rescue of V5-002 and NOT a rescue of V3 Candidate B.

## Population

Use the V5-002B all-breakout population, but only lower-scale events:

```text
60m breakout events
240m breakout events
```

1440m events are not used in V5-003A because this study specifically requires a pre-registered higher context scale.

## Causal context scales

For each 60m breakout:
- 240m context;
- 1440m context.

For each 240m breakout:
- 1440m context.

Every context window is `[t-C,t)` and excludes the event M1 bar.

## Context variables

For breakout direction `d in {-1,+1}`:

```text
context_alignment_efficiency
= d * sum(log returns in context) / sum(abs(log returns in context))
```

Interpretation:
- positive: higher context is directionally efficient in the breakout direction;
- near zero: noisy/balanced;
- negative: efficient movement opposite the breakout.

Also record:
- absolute context efficiency;
- context range/previous-range log contrast;
- context RV/previous-RV log contrast;
- absolute context range/RV level.

No threshold such as `ER > 0.3` is allowed.

## Primary outcomes

To prevent confirmation from receiving credit for movement already consumed:

For 60m breakout events:
- signed remaining return from 5m -> 60m;
- signed remaining return from 5m -> 240m.

For 240m breakout events:
- signed remaining return from 5m -> 240m.

All are normalized as return to pre-event price, not divided by the range.

## Primary claim

Higher-timeframe `context_alignment_efficiency` adds positive information about **remaining continuation in breakout direction**
after controlling for lower-timeframe state.

Controls:
- event-scale pre-alignment efficiency;
- event-scale RV level;
- event-scale range/price;
- event-scale expansion contrast;
- event 5m displacement;
- hour-of-day.

## Required decomposition

Report every:
- symbol;
- year;
- direction;
- event scale;
- context scale.

No best-market, best-direction, or best-context-scale selection.

## Negative control

Permute context alignment inside:

```text
symbol x year x direction x event-scale x context-scale x hour-of-day
```

The real relationship must exceed the time-of-day-preserving null.

## Promotion gate for a later semantic candidate

No pullback/reload study opens unless:

1. primary partial relationship is positive in at least 18/24 symbol-year-direction groups for 60m events with 240m context;
2. the 60m->1440m context has the same positive median sign and is positive in at least 16/24 groups;
3. remaining 240m results do not reverse the relationship;
4. 240m events with 1440m context do not show a material sign reversal;
5. observed summary exceeds the 95th percentile of the permutation control;
6. no one market/year is required for the effect.

Failure closes V5-003A. Do not rescue with ER thresholds.

## If it passes

Only then pre-register V5-003B:
`established directional expansion -> first pullback -> continuation/failure geometry`.

No V3 liquidity/FVG/reload gates are inherited.
