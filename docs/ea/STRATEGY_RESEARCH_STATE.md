# Strategy Robustness Research State

Last updated: 2026-08-19
Status: ACTIVE
Baseline: Mentor deterministic V1 / build 1.91
Purpose: discover where the current method actually has edge before adding strategy complexity

## 1. Why this research exists

The EA has reached a point where most of the causal execution pipeline is implemented and long-run execution performance is practical.

The remaining strategic problem is not simply "find better parameters."

Long-run tests show strong instability:

```text
2023 closed result ≈ +44.94R
2024 closed result ≈ -36.56R
2025 closed result ≈ +8.68R
```

The 2024 number is not a clean final profitability result because the two-year run ended with open exposure and contained one execution divergence. However, removing that one execution anomaly does not explain the broad 2024 weakness.

The same nominal strategy therefore behaves very differently across market periods.

This creates two distinct possibilities:

1. the strategy concept has regime-dependent edge;
2. the upstream detectors are producing technically causal but semantically poor market objects.

Both must be investigated before parameter optimization.

## 2. Important long-run observations

### 2025

```text
58 closed trades
14 TP / 44 SL
win rate ≈ 24.1%
realized ≈ +8.68R

EXTERNAL_CONTINUATION ≈ +15.94R
EXTERNAL_REVERSAL ≈ -7.26R
```

Reversal was weak, but this alone does not explain the multi-year instability.

### 2023 versus 2024

Preliminary two-year research summary:

```text
2023:
70 closed trades
23 wins
win rate ≈ 32.9%
≈ +44.94R

2024:
56 closed trades
5 wins
win rate ≈ 8.9%
≈ -36.56R
```

By scope:

```text
2023 continuation ≈ +48.31R
2023 reversal     ≈  -3.37R

2024 continuation ≈ -29.46R
2024 reversal     ≈  -7.10R
```

Therefore "turn reversal off" is not a sufficient explanation or solution.

### Equity-curve character

A cross-year analysis snapshot, excluding the known divergence trade where appropriate, showed approximately:

```text
183 clean closed trades across 2023-2025
aggregate ≈ +18.1R
positive months = 13 / 36
monthly R median ≈ -1.65R
longest losing streak = 22
top 10 winners ≈ 54% of all positive R
```

This indicates a low-win-rate, tail-dependent system rather than the desired steadily rising equity curve.

These figures are research evidence, not an approved strategy result.

## 3. Core concern: implementation correctness is not semantic validity

A detector can be perfectly causal and still identify the wrong thing.

Examples of current concerns:

### Structure / trend

Questions:
- Does the three-opposite-candle wave mechanism select swings a human would regard as important?
- Does the BOS-producing correction really deserve protected-swing ownership?
- Is a body close through the current structural level sufficient to characterize directional persistence?
- Does the H1/M30 map remain bullish or bearish long after a human would say the market has entered distribution, compression, transition, or opposing displacement?
- Are we confusing "the previous structure has not officially broken" with "continuation still has positive expectancy"?

The current TradingView regime visualization already suggests that directional state can persist through visually different market conditions.

This is a research observation, not yet a rule change.

### Liquidity

Questions:
- Are EXTERNAL_SWING pools visually obvious highs/lows or merely mechanically retained structural points?
- Are some pools too old to remain meaningful?
- Can an apparently active pool already have been economically resolved even if the exact coded consumption rule has not fired?
- Are defended-range edges genuinely defended ranges or incidental overlapping wicks?
- Does a one-tick penetration/recovery of a weak pool deserve the same Sweep semantics as a clear liquidity raid?

### Root OB

Questions:
- Does `LAST_OPPOSITE_OB` identify a causal source candle or sometimes an arbitrary opposite candle inside chop?
- Does `FVG_ORIGIN_OB` identify a meaningful origin or merely increase Root count?
- When multiple Roots explain the same downstream Entry, are those Roots genuinely independent causal structures or duplicate explanations of the same move?
- Is full-candle OB geometry appropriate for every recognized Root?
- How should consolidation-origin candles be distinguished from meaningful displacement origins without inventing an overfit score?

### Regime / directional authority

The current V1 "regime" should be understood accurately:

```text
it is primarily H1/M30 structure-based directional authorization,
not a complete market-regime classifier.
```

It does not directly classify:
- trend versus range,
- expansion versus compression,
- high versus low directional persistence,
- trend maturity/exhaustion,
- clean versus overlapping/choppy structure,
- volatility regime.

Therefore:

```text
H1 bullish structure
!=
proof that LONG continuation currently has positive expectancy
```

The research goal is not to perfectly predict the true market regime.

The useful goal is:

> identify observable, causal market states in which the current setup's expectancy changes consistently.

A future regime representation may be multidimensional rather than one Bull/Bear label, for example direction, persistence, expansion/compression, maturity, structure cleanliness, and location. These are hypotheses only; no such filter is currently authorized.

### Sweep

Questions:
- Is the swept pool itself meaningful?
- Is one tick of penetration enough in practice?
- Does the recovery close show rejection or merely noise?
- Does Sweep quality depend more on the pre-existing liquidity structure than on penetration size?
- Are clear raids and trivial wick excursions currently treated as equivalent?

### CHoCH

Questions:
- Does every M1 protected break deserve the same confirmation authority?
- Is a slow overlapping break equivalent to a displacement break?
- Does the current protected swing itself make visual sense?
- Is the CHoCH late because the upstream protected level is stale?
- Is CHoCH confirming local order-flow change or simply reacting after most of the move is already complete?

Do not immediately convert these questions into body-size or time thresholds.

First determine whether systematic visual differences exist.

### FVG

Questions:
- Are the causal FVGs inside accepted Sweep→CHoCH legs visually meaningful?
- Is "widest eligible FVG" economically justified or only deterministic?
- Would first, last, CHoCH-adjacent, or overlapping FVGs better represent the displacement?
- Are large/small FVG properties stable across years?

Again, no selection rule should change until upstream semantic validity is established.

## 4. Why regime is the first major research priority

The direction map sits above nearly the entire trade chain.

If the map says LONG in a market where continuation expectancy is poor, every downstream component can behave exactly as coded and still produce bad trades.

The current system effectively asks:

```text
Is H1 a mature bullish/bearish structure?
If not, can M30 provide direction?
Has H1 reversal permission opened?
```

This is useful structural state, but it may be too coarse and too persistent to represent the trading environment.

The research problem should therefore be framed as:

Bad question:
"Can we perfectly label the market Bull/Bear/Range?"

Better question:
"Under which causal market states does our existing LONG or SHORT setup retain positive expectancy?"

This allows an explicit `NO CLEAR EDGE` state rather than forcing a direction at all times.

## 5. Research method

### Stage A — visual semantic audit

Use a TradingView display-only indicator to overlay the current pipeline:

```text
causal waves
structure events
protected/external levels
liquidity
Root OB
H1/M30 directional regime
Root contact
M1 Sweep
M1 CHoCH
M1 FVG
```

Purpose:
- verify that the objects are meaningful to a human observer;
- find repeated classes of obvious mismatch;
- understand whether poor trades start with a bad market object or fail later.

The indicator is not strategy authority and is not exact MT5 feed parity proof.

### Stage B — cross-period sampling

Inspect multiple independent periods from:
- strong 2023 segments,
- weak 2024 segments,
- mixed 2025 segments.

Avoid selecting only spectacular winners and losers.

Where possible:
- sample dates before looking at trade outcome;
- record whether the structure/liquidity/Root/regime appears meaningful;
- compare the same criteria across all years.

### Stage C — mismatch taxonomy

Create a small set of recurring failure categories, for example:

```text
STRUCTURE_TOO_LATE
STRUCTURE_CHOP_FALSE_DIRECTION
LIQUIDITY_STALE
LIQUIDITY_NOT_VISUALLY_SIGNIFICANT
ROOT_CONSOLIDATION_NOISE
ROOT_NOT_CAUSAL_DISPLACEMENT
SWEEP_TRIVIAL
CHOCH_WEAK_OR_LATE
REGIME_DIRECTION_WITHOUT_PERSISTENCE
```

These names are examples, not current rules.

The goal is to discover recurring mechanisms, not to invent labels for every losing trade.

### Stage D — causal measurement

Only after a repeated visual mechanism is identified:
- add causal audit fields to the EA/event log;
- measure the phenomenon over several years;
- study continuous relationships before choosing thresholds;
- check whether the relationship has the same sign across independent years.

### Stage E — minimal research variant

One meaningful change at a time.

Compare against the frozen baseline on the same periods and data model.

Evaluate:
- expectancy R,
- annual consistency,
- rolling 3/6-month R,
- maximum R drawdown,
- losing streak,
- trade count,
- direction/scope stability,
- dependence on a few large winners.

Do not accept a rule merely because total R increases.

## 6. What not to do

Do not:
- repair 2024 with a hand-picked threshold;
- automatically remove SHORT, M30, FVG-origin OB, or add-ons;
- add many generic indicators and call the combination "regime";
- introduce a quality score before its components show stable information;
- use future price action to label a real-time regime transition;
- let winner/loser outcomes define what a "good-looking" structure must be;
- deploy ML before verifying that the base labels are meaningful.

Machine learning, clustering, HMMs, or change-point models may become useful later, but only after the observable market objects themselves are trustworthy.

## 7. Current visual-audit tool

A separate TradingView `Mentor V1 Pipeline Visual Audit` Pine indicator is under local compile/visual validation.

Current intended scope:
- M1 host chart,
- H4/H1/M30/M15/M5/M1 reconstructed context,
- structure / liquidity / Root / regime / Sweep / CHoCH / FVG visualization,
- no orders,
- no SL/TP recommendation,
- no strategy change.

Do not treat this local indicator as repository authority until its Pine compile and visual behavior are validated and it is intentionally committed.

## 8. Parallel execution-safety item

The build-1.91 multi-year run exposed one remaining broker-lifecycle edge case:
recoverable pending cancellation rejection is not retried.

This should be fixed separately from strategy research.

A clean multi-year profitability baseline requires:
- no execution divergence,
- no orphan pending,
- tester-end exposure handled consistently.

Visual semantic research can continue in parallel because the one broker edge case does not explain the broad cross-year strategy instability.

## 9. Next session start point

After reading `AGENTS.md` and `HANDOFF.md`, continue here.

Immediate research task:

> Use the visual audit to determine whether structure, liquidity, Root OB, and directional regime are human-meaningful before changing any entry/exit parameter.

The first major hypothesis to challenge is:

> H1/M30 structural direction alone is too coarse to serve as a trading regime.

Do not assume the hypothesis is true. Attempt to falsify it using cross-year chart evidence.
