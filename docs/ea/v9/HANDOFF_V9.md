# V9 Development Handoff

Last updated: `2026-09-15`
Status: `PROTOTYPE FROZEN / ACTUAL-TICK VALIDATED / TERMINAL-STAGE SHADOW RESEARCH NEXT`
Production authority: `NONE`
EA authority: `RESEARCH / DEMO ONLY`

## Resume point

Do not return to broad entry-feature mining.
Do not alter the current prototype from the new Heikin-Ashi research.

There are now two separate lanes:

```text
A. execution lane
current frozen prototype -> EA R1 -> forward demo

B. strategy-research lane
terminal-stage causal detection -> HA arming study -> sequential economic validation
```

The strategy-research lane is the immediate research focus requested by the user.

## Current prototype remains unchanged

- H1/H4 liquidity geometry: causal 2-left / 2-right.
- Entry authorization: causal PRIMARY_ACTIVE H4-liquidity Arrival.
- H1 Hard SL: nearest active opposite H1 swing liquidity.
- ERA scale: previous-completed H4 Wilder ATR180.
- Eligibility: `ERA_RISK <= 4`; never clip/move structural SL inward.
- First accepted Child in route: ANCHOR; current exit at CHALLENGE_OPENS unless own SL first.
- Later accepted Children: CONTINUATION; current exit at next H4-liquidity Arrival unless own SL first.
- No fixed TP, SHORT ban, Child-count cap, day/session/hour filter, or duration timeout.

## Current validated execution baseline

MT5 actual-tick reference through `2026-08-28`:

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

Actual-tick execution remains higher authority than M1 for chronology/fills.

## Latest consumed-data exit research

### 1. HA from Anchor entry

H4 Heikin-Ashi opposite-color exits reduce giveback but cut the Anchor right tail when armed immediately after Anchor entry.

On the deterministic `295`-Anchor common population:

```text
BASE CHALLENGE
+4,194.36 / PF 2.331 / median hold 70.6h / median giveback 2.20 ATR180

HA1 from entry
+2,089.18 / PF 1.965 / median hold 19.2h / median giveback 1.25 ATR180

HA2 from entry
+2,490.10 / PF 2.013 / median hold 27.9h / median giveback 1.52 ATR180
```

HA itself is not the main failure. Activation from the beginning of a long multi-Child journey is too early.

### 2. Hindsight terminal activation oracle

A deliberately non-causal oracle then arms HA only after the route's **true last accepted Child**.

On the deterministic role-based population of `1,139` resolved Children:

| Policy | PnL | PF | WR | DD |
|---|---:|---:|---:|---:|
| BASE role policy | +8,530.74 | 2.023 | 65.58% | 440.35 |
| last-Child oracle -> HA1, Anchor only | +12,173.84 | 2.732 | 68.83% | 328.57 |
| last-Child oracle -> HA2, Anchor only | +11,167.85 | 2.505 | 67.52% | 355.54 |
| **last-Child oracle -> HA1, all still-open Children** | **+13,863.22** | **3.475** | **70.41%** | **288.75** |
| last-Child oracle -> HA2, all still-open Children | +12,102.57 | 2.853 | 68.83% | 289.85 |

For HA1 all-open, all five entry years improved versus BASE:

```text
2022 +234.66 ->   +914.82
2023 +867.71 -> +1,322.78
2024 +1,287.89 -> +2,001.39
2025 +2,711.21 -> +4,244.12
2026 +3,429.27 -> +5,380.11
```

By role under HA1 all-open:

```text
ANCHOR        +4,194.36 -> +7,837.46
CONTINUATION  +4,336.38 -> +6,025.76
```

By direction:

```text
UP    +6,969.65 -> +9,904.71
DOWN  +1,561.09 -> +3,958.51
```

This is an oracle upper bound only. `true last Child` is future information.

## Interpretation

The research question is no longer `Is HA a good exit?`.

Current evidence supports:

```text
mid-journey opposite HA
= often normal pullback
= dangerous hard exit

terminal-participation opposite HA
= potentially strong profit-protection event
```

The difficult problem is the **activation state**, not the HA formula.

## Next research

Use:

`V9_NEXT_RESEARCH_CONTRACT_TERMINAL_STAGE_CAUSAL_DETECTION_20260915.md`

Primary objective:

> Estimate terminal participation with only causally known information, then arm H4 HA1/HA2 and test the resulting policy sequentially.

Required comparisons:

1. mechanical H4-liquidity baselines;
2. simple logistic / shallow tree;
3. nonlinear model only if it adds stable information;
4. final route-sequential PnL/PF/DD/right-tail comparison, not checkpoint AUC alone.

Do not create `N-th Child`, elapsed-time, fixed-distance, or direction-specific rules from the oracle slices.

## Execution lane remains open

The existing forward-demo contract remains valid for the unchanged prototype. Any terminal-stage/HA candidate must remain shadow-only until it earns separate causal evidence and then actual-tick/forward validation.
