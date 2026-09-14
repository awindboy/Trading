# V9 Actual-Tick Execution and Era-Scale Addendum

Date: `2026-09-14`
Status: `ACTIVE ADDENDUM / OVERRIDES CONFLICTING OLDER EXECUTION-SCALE TEXT`

## 1. Tick execution precedence

For execution-grade questions, actual tick chronology outranks M1 intraminute inference.

Raw M1 remains authoritative for long-span source reconstruction where tick history is unavailable, but an M1 high/low must not be used to invent ordering among multiple intraminute liquidity/SL/semantic events when actual ticks are available.

## 2. Multiple H4 liquidity raids

Distinct H4 liquidity raids reached on distinct Bid ticks are distinct Arrivals, even when they occur inside the same M1 minute.

This supersedes the research convenience of collapsing all same-minute same-side H4 raids into one Arrival.

## 3. Structural/executable side convention

Current EA research convention:

```text
liquidity / structural chronology -> Bid
LONG executable entry -> Ask
SHORT executable entry -> Bid
LONG executable exit -> Bid
SHORT executable exit -> Ask
```

Every semantic reference and actual fill must be logged separately.

## 4. ERA coordinate

The old fast coordinate may remain descriptive:

```text
S_FAST(t) = previous completed H4 Wilder ATR14
```

The current structural-risk eligibility coordinate is:

```text
ERA_SCALE(t) = previous completed H4 Wilder ATR180
ERA_RISK     = structural SL distance / ERA_SCALE(t)
```

Current prototype entry authority includes `ERA_RISK <= 4`.

Therefore older statements that “no ATR threshold has entry authority” are superseded **only for this explicit ERA4 rule**. Do not generalize that exception to other ATR thresholds.

## 5. Data locks

Old `2025-07 LOCKED` and `2021 reserve` statements are superseded by explicit user authorization to use all available data. Causal replay rules remain unchanged.

## 6. Ambiguity

Where actual tick order is available, resolve the order from ticks.

Where it is not available, remain fail-closed/ambiguous; do not assign favorable ordering.
