# V9 Research State

Date: `2026-09-15`
Status: `PROTOTYPE FROZEN / ACTUAL-TICK VALIDATED / TERMINAL-STAGE SHADOW RESEARCH ACTIVE`
Market: `GOLD# ONLY`

## Current mechanical thesis

The current prototype remains:

```text
Arrival / Delivery Grammar
+ H1 structural invalidation
+ H4 ATR180 long-era normalization
+ ERA_RISK <= 4
+ ANCHOR / CONTINUATION role split
+ tick-native execution
```

No latest shadow result changes strategy authority.

## Current validated baseline

### M1 role-based research population

Deterministic resolved role-based population used for the latest exit studies:

```text
1,139 resolved Children
BASE PnL +8,530.74
PF 2.023
WR 65.58%
DD 440.35
```

This is consumed-data M1/H4 screening, not the actual-tick production comparator.

### Actual MT5 real ticks

Reference through `2026-08-28`:

```text
1,316 closed
+5,028.62
PF 1.425
WR 60.18%
```

Full uploaded closed ledger through September:

```text
1,322 closed
+4,954.61
PF 1.412
WR 60.14%
```

By direction in that actual-tick ledger:

```text
UP    +4,836.20 / PF 1.832
DOWN    +118.41 / PF 1.019
```

SHORT weakness remains diagnostic, not permission for a SHORT ban.

## Research progression leading to the current question

### A. HTF movement-capacity shadow research

V8-style directionless movement probability transferred to H4 reasonably well when targets/distances were normalized with the V9 long-era coordinate. The most useful form was not an absolute probability threshold but route-relative movement-capacity change.

It did not become exit authority. Directional continuation models remained much weaker and unstable.

### B. Journey-end shadow classification

The question `is this the final same-side H4 liquidity before challenge?` showed usable but imperfect information.

The strongest simple feature was the remaining nearest same-side H4 liquidity distance normalized by previous-completed H4 ATR180. Complex H1-chart ML did not consistently beat simple H4 liquidity geometry.

This classification was not sufficient as a direct first-trigger exit because checkpoint false positives accumulate inside long journeys and cut the right tail.

### C. Heikin-Ashi from Anchor entry

H4 Heikin-Ashi did what the chart intuition suggested: it smoothed ordinary candle-color noise and reduced peak-to-exit giveback.

However, arming it from Anchor entry cut normal pullbacks inside large journeys.

On `295` deterministic Anchors:

```text
BASE CHALLENGE  +4,194.36 / PF 2.331
HA1 from entry  +2,089.18 / PF 1.965
HA2 from entry  +2,490.10 / PF 2.013
```

Median giveback nevertheless improved:

```text
BASE 2.20 ATR180
HA1  1.25 ATR180
HA2  1.52 ATR180
```

Therefore HA contains useful weakening information but lacks the correct activation context.

## Terminal-stage last-Child oracle

A hindsight upper-bound experiment arms HA only after the route's **true last accepted Child**. This is explicitly non-causal and cannot be traded as written.

### Strategy-wide result — all still-open Children closed on terminal HA

| Policy | N | PnL | PF | WR | DD |
|---|---:|---:|---:|---:|---:|
| BASE | 1,139 | +8,530.74 | 2.023 | 65.58% | 440.35 |
| terminal oracle HA1 | 1,139 | **+13,863.22** | **3.475** | **70.41%** | **288.75** |
| terminal oracle HA2 | 1,139 | +12,102.57 | 2.853 | 68.83% | 289.85 |

HA1 changed `320` deterministic Child exits:

```text
211 ANCHOR
109 CONTINUATION
```

HA2 changed `247`:

```text
168 ANCHOR
79 CONTINUATION
```

### Year robustness of HA1 oracle

```text
2022  +234.66 ->   +914.82
2023  +867.71 -> +1,322.78
2024 +1,287.89 -> +2,001.39
2025 +2,711.21 -> +4,244.12
2026 +3,429.27 -> +5,380.11
```

All five entry years improve in the oracle screen.

### Role effect

```text
ANCHOR
+4,194.36 -> +7,837.46
PF 2.331 -> 5.254

CONTINUATION
+4,336.38 -> +6,025.76
PF 1.836 -> 2.603
```

This means the potential benefit is not limited to Anchor profit protection. Once the route is truly terminal, the final still-open Continuation can also benefit from the same HA event.

### Direction effect

```text
UP
+6,969.65 -> +9,904.71
PF 2.826 -> 4.938

DOWN
+1,561.09 -> +3,958.51
PF 1.345 -> 2.283
```

The oracle benefit exists on both sides; do not turn it into a direction-specific rule.

### Journey type

Using the full accepted-Child count per route on the deterministic resolved ledger:

```text
SINGLE routes: 65
BASE -952.33 -> HA1 -281.54

MULTI routes: 237
BASE +9,483.07 -> HA1 +14,144.76
```

The crucial reversal versus HA-from-entry is that terminal activation no longer destroys multi-Child right-tail journeys.

## What the oracle does and does not prove

It supports this hypothesis:

> HA may be a strong termination/profit-protection mechanism **after** V9 has entered a terminal-participation state.

It does not prove:

- that the last accepted Child can be known live;
- that any fixed Child number defines terminal state;
- that HA1 should replace current exits now;
- that M1/H4 close-price economics survive real Bid/Ask and actual-tick execution;
- that historical oracle improvements are forward edge.

## Active research question

The next problem is:

```text
CAUSAL TERMINAL-STAGE DETECTION
```

At each newly accepted Child / same-side H4 Arrival, estimate whether the current route has likely reached the stage where no additional accepted Child will be earned before challenge.

Candidate inputs must already be known:

- nearest remaining same-side H4 liquidity distance / ATR180;
- opposite H4 liquidity distance / ATR180;
- same/opposite distance ratio and topology;
- active H4 liquidity counts/ages;
- consumed-liquidity age and route delivery history;
- Anchor MFE, giveback, realized expansion / ATR180;
- route-relative movement-capacity level/change;
- completed H1 range/volatility/efficiency context;
- current position/role state.

Do not use future `last Child`, later price path, eventual challenge, or final PnL as features.

## Required evaluation

The next study must distinguish:

```text
checkpoint classification quality
!=
sequential exit-policy quality
```

A candidate succeeds only if a causal arming policy followed by frozen HA1/HA2 logic improves the route/trade ledger without destroying large-winner capture.

Primary economic comparison remains BASE role policy on the same causal population.

## Open risks

- every supplied historical period is consumed; future proof must ultimately be prospective;
- actual-tick sequencing/fills are higher authority than H4 close-price screening;
- terminal-stage model selection can easily overfit Child count, route age, or 2026 large moves;
- HA close execution around market gaps requires separate actual-tick/forward validation;
- existing forward-demo execution contract remains necessary even if a shadow exit candidate looks strong.
