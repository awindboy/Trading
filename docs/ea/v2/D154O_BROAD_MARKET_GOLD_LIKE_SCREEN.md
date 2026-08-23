# D-154O — Broad-Market Gold-Like Execution-Suitability Screen

Status: ACTIVE RESEARCH CONTRACT / OUTCOME-BLIND SCREEN  
Date: 2026-08-24  
Primary environment: XM Ultra Low  
D154N status: DEFERRED, not rejected

## 1. Why the research direction changes

D154K/L/M/UL established a reproducible execution-scale relationship:

```text
lower spread relative to the strategy's local price geometry
-> generally better cross-market Entry survival
```

Ultra Low confirmed that reducing spread can improve actual outcomes and reduce D154M quote-side flips. But trying to make very high-friction markets such as CADJPY or SILVER perform like GOLD may not be the highest-value research objective.

The next question is therefore:

> Does the V2 continuation strategy reproduce GOLD-like Entry survival on other markets whose execution friction is naturally GOLD-like relative to their local price movement?

If yes, the strategy should prioritize a compatible market universe instead of forcing one Entry architecture onto every tradable symbol.

## 2. Core hypothesis

Market-level hypothesis:

```text
GOLD-like execution scale
-> materially higher probability that the current deterministic V2 Entry architecture retains its edge
```

This is a market-universe / environment hypothesis.

It is **not**:

```text
if current spread > threshold:
    reject this individual trade
```

No per-trade spread gate is authorized.

## 3. Two-stage research architecture

### Stage A — one-week chart-only pre-screen

Purpose:
- screen a large Ultra Low symbol universe cheaply;
- do not require the EA to generate a trade;
- do not look at strategy win rate or P/L;
- identify markets whose raw execution scale resembles GOLD#.

The user will provide the candidate Ultra Low symbol list in the next session.

Frozen screen week:

```text
2026-08-17 00:00
through
2026-08-23 23:59
```

Use broker/server timestamps consistently.

Use the same calendar window for every symbol.

Closed-market minutes are not failures and are not padded with synthetic bars.

### Stage B — one-year strategy confirmation

After Stage A:
1. freeze the Gold-like shortlist before seeing one-year strategy outcomes;
2. freeze a small negative-control cohort before seeing outcomes;
3. run 2025 real-tick V2 baseline + D151/D154K/D154M measurements;
4. test whether Gold-like markets actually reproduce better Entry survival.

Do not add/drop markets after their one-year result becomes known.

## 4. Important metric distinction

The original strategy-derived D154K variables are:

```text
spread / causal Root-contact->CHOCH reaction TR
spread / actual 1R
spread / selected causal FVG width
```

These cannot all be measured faithfully from one week of raw chart data without actual strategy setups/fills.

Therefore Stage A MUST NOT relabel a raw chart proxy as the exact D154K metric.

### Stage A raw proxies

Preferred required data:
- M1 timestamp;
- open/high/low/close;
- spread in points;
- symbol point size / digits;
- tick volume if available.

If direct tick Bid/Ask data can be collected cheaply, retain it as higher-quality supplemental evidence, but it is not required for the first broad screen.

#### Raw proxy A — spread relative to M1 movement

For each valid M1 bar:

```text
spread_price = spread_points * point
TR = max(
    high - low,
    abs(high - previous_close),
    abs(low - previous_close)
)
```

Do not use the first bar after a session/data gap larger than 5 minutes for TR because the gap would artificially inflate local movement scale.

Report at minimum:

```text
weekly median spread_price
weekly median valid M1 TR
raw_spread_over_m1_tr = median_spread / median_TR
```

Also retain daily values and distribution quantiles so one unusually liquid hour cannot define the market.

#### Raw proxy B — spread relative to generic M1 FVG geometry

From all causally identifiable three-bar M1 FVGs during the screen week:

Bullish raw FVG:
```text
bar3.low > bar1.high
width = bar3.low - bar1.high
```

Bearish raw FVG:
```text
bar3.high < bar1.low
width = bar1.low - bar3.high
```

Use the spread associated with the third bar when the FVG becomes known.

Report:

```text
raw M1 FVG count
median raw FVG width
median spread / raw FVG width
```

This is an **all-M1-FVG proxy**, not the selected causal strategy FVG.

If there are too few valid FVG observations, mark the FVG proxy `INSUFFICIENT`, not zero.

#### Raw proxy C — absolute friction

Report:

```text
median spread / close price
```

preferably in basis points.

This guards against a symbol looking favorable only because its nominal price scale is large.

## 5. Data-quality rules

A symbol is not eligible for screening if data quality is inadequate.

Record:
- active trading days;
- number of valid M1 bars;
- missing spread fraction;
- zero/invalid price fraction;
- valid TR count;
- raw FVG count;
- symbol point and digits.

Do not rank an `INSUFFICIENT_DATA` symbol as good or bad.

No synthetic filling of missing bars.

## 6. Same-week GOLD# is the reference

GOLD# must be included in the exact same one-week dataset.

Every raw screen result is reported both absolutely and relative to GOLD#:

```text
symbol raw_spread_over_m1_tr / GOLD# raw_spread_over_m1_tr

symbol raw_spread_over_raw_fvg / GOLD# raw_spread_over_raw_fvg

symbol spread_bps / GOLD# spread_bps
```

This reduces dependence on whether the chosen week happened to be unusually volatile or quiet.

## 7. No premature combined quality score

Do not create a weighted `GoldLikeScore`.

Keep the raw dimensions visible separately.

After the full universe's Stage-A measurements are available, a shortlist rule may be frozen using only:
- raw execution metrics;
- their distributions;
- data quality;
- tradeable asset/category context.

One-year strategy outcomes must still be hidden/unrun at that point.

The exact shortlist manifest and its selection rationale must be saved before Stage B.

## 8. Negative controls are mandatory

Running only the best-looking markets would weaken the causal test.

Stage B therefore includes:

```text
all frozen Gold-like candidates
+
a small frozen non-Gold-like control cohort
```

Target control size:
- approximately 2-4 symbols if runtime permits;
- selected before outcome;
- preferably include asset-class-matched controls where practical.

Existing SILVER# and CADJPY# remain useful known high-friction historical controls, but at least some newly screened non-Gold-like controls are preferable if the universe is large enough.

## 9. Stage-B 2025 full-year test

Environment:

```text
XM Ultra Low
Every tick based on real ticks
2025-01-01 .. 2025-12-31
```

Baseline/research settings remain unchanged:
- continuation-only;
- V3E mode 9 as current post+1R reference;
- EM OFF;
- D151 ON;
- D154K ON;
- D154M ON;
- no new Entry gate.

For every shortlisted/control market report:

### Entry-survival
```text
Fill count
PLUS_1R
SL_FIRST
right-censored
Fill->+1R survival
LONG/SHORT survival
```

### Exact D154K execution geometry
```text
median spread / causal reaction TR
median spread / actual 1R
median spread / selected causal FVG
risk / reaction TR
FVG / reaction TR
```

### D154M
```text
actual survival
entry-side quote shadow survival
SL_FIRST -> shadow PLUS_1R count/rate
```

### Strategy-level secondary evidence
Keep separate from Entry survival:
```text
realized V3E WR
average winner R
expectancy R
drawdown / loss streak if available
```

## 10. Trade-frequency guard

A market with almost no strategy opportunities cannot validate the hypothesis.

Do not treat a high observed WR from a tiny Fill count as a success.

Report sample size prominently.

If the candidate has insufficient 2025 fills for a meaningful conclusion:
```text
status = INSUFFICIENT_STRATEGY_SAMPLE
```

Do not rescue it by extending/shortening the period after seeing results.

## 11. Hypothesis outcomes

### Case A — Gold-like markets generally reproduce good survival

Example qualitative result:

```text
Gold-like cohort:
multiple independent markets around or above 50% Entry survival

non-Gold-like controls:
materially weaker survival
```

Interpretation:
- execution suitability is likely an important market-universe condition;
- stop prioritizing rescue of structurally incompatible high-friction markets;
- research future Entry/exit improvements primarily on the compatible universe.

### Case B — Gold-like markets show mixed/poor outcomes

Interpretation:
- low friction is likely necessary/helpful but not sufficient;
- next research target becomes underlying market regime/path quality inside the low-friction cohort.

### Case C — broader universe breaks the relation

Interpretation:
- the four-market D154L/UL relation may have been asset/sample-confounded;
- do not build a market-eligibility layer from it.

## 12. Temporal confirmation before permanent market eligibility

A positive 2025 cross-market result is strong evidence but is not enough for permanent strategy authority.

Before a `market eligibility layer` becomes part of production strategy:
- use an additional disjoint year where Ultra Low real-tick history is available;
- preserve the Stage-A/Stage-B selection rule;
- confirm the relationship does not reverse.

Do not promote a one-year screen directly to permanent symbol authorization.

## 13. D154N disposition

D154N pending-to-Fill quote-side delay/depth audit is:

```text
DEFERRED
not rejected
not deleted
```

Reason:
- if enough Gold-like markets already reproduce the edge, detailed rescue of high-friction markets has lower strategic value;
- if the broad market screen fails, D154N may still help separate execution from underlying path quality.

D154N should not run before D154O Stage-B interpretation unless new evidence changes the priority.

## 14. Immediate next-session task

1. Re-read GitHub authority and this contract.
2. User supplies the broad Ultra Low symbol list.
3. Build a batch/export workflow for the frozen week.
4. Collect M1+spread+metadata for all supplied symbols.
5. Compute the outcome-blind raw screen.
6. Freeze shortlist + controls manifest.
7. Only then prepare one-year Strategy Tester batches.

No one-year outcome should be generated before step 6.
