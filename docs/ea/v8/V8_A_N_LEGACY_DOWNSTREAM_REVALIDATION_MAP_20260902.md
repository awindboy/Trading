# V8-A-N Legacy M5-N1 Downstream Research — Revalidation Map — 2026-09-02

Status: `HISTORICAL DEVELOPMENT EVIDENCE / HYPOTHESIS SOURCE / SLOW-N REVALIDATION REQUIRED`
Population: old `1.50 * M5 ATR14 fresh P15 75-cross`
Years: `2024-2026 consumed development evidence`
Reserve: `GOLD# 2021 untouched`

## 1. Purpose of this document

A large amount of direction research was performed after the old M5-A-N N1 was frozen. The active A-N target semantics are now being reset to a slow H4-scale formulation.

This document prevents two opposite errors:

1. **do not carry old percentages into Slow-N as if the population were unchanged**;
2. **do not throw away useful falsifications, instrumentation and mechanistic hypotheses** merely because the trigger population changes.

Every number below is conditional on the legacy M5-A-N N1 unless explicitly stated otherwise.

## 2. Legacy population and N2 baseline

Old resolved direction ledger:

```text
2024 797
2025 814
2026 538
ALL 2149
```

Official N2-R1 had to be recomputed from seven unique votes because an older stored ledger accidentally double-counted P60.

Official development accuracy:

```text
2024 57.34%
2025 57.62%
2026 57.43%
```

N2-R1 is post-hoc maximin development control only. It also contains an old M5-A-N P60 vote, so it is not a native Slow-N rule.

## 3. Deterministic chart-voter research

### 3.1 Initial semantic 7-voter panel

Panel:

1. M5 MA state;
2. M5 Stochastic(14,3,3);
3. M5 RSI14;
4. M5 MACD;
5. M5 DMI14;
6. M5 price action;
7. M15/H1/H4 causal EMA20>EMA50 MTF state.

Final majority accuracy:

```text
2024 49.56%
2025 51.60%
2026 50.93%
```

Conclusion: correlated technical-voter herding did not solve direction.

M5 Stoch K/D cross direction alone was modest:

```text
2024 56.63% N249
2025 56.73% N245
2026 54.38% N160
```

### 3.2 Oracle/pattern audit

The correct-voter count was strongly U-shaped; voters often herded together correctly or incorrectly. Exact categorical pattern memorization and 2024-frozen pair/triple maps transferred poorly.

Some attractive motifs were post-hoc and multiplicity-exposed. Do not promote them.

### 3.3 MTF expansion

M5/M15/M30/H1/H4 timeframe/role/holistic panels remained roughly 49-52%.

Mechanical adjacent-timeframe expansion increased redundancy rather than edge.

A notable asymmetric state:

```text
M15 structure LONG
M30 structure LONG
HTF regime SHORT
location LONG
```

UP-first accuracy:

```text
2024 58.21% N67
2025 60.00% N55
2026 62.00% N50
```

The symmetric downside state failed. Multiple-testing audit showed that many small chart-state combinations could arise by chance. Retain only as a hypothesis.

### 3.4 Market-question redesign

Seven less-redundant questions were built: immediate pressure, oscillator transition, M15 structure, HTF regime, volatility transition, location/liquidity, and M1 tape proxy.

Equal panel:

```text
2024 49.94%
2025 51.11%
2026 51.86%
```

Hierarchical/shallow-tree variants did not materially improve.

### 3.5 Specialist abstention fusion

Using Stoch cross / refined MTF / structure propagation specialists to override N2-R1 did not create stable improvement.

Conclusion before ticks: new information was required.

## 4. Raw tick research

### 4.1 V1/V2/V3 invalidation

Early normalized tick probes converted ledger timestamps through `Europe/Helsinki -> UTC`, but MT5 tick lookup needed the ledger/M1 wall-clock directly.

The error shifted tick windows by ~2h winter / ~3h summer.

Evidence came from raw tick-count versus source M1 TICKVOL activity correlation and missing-window patterns.

All V1/V2/V3 tick performance results are discarded.

### 4.2 V4 alignment authority

V4 used direct UTC/wall-clock lookup and fail-closed alignment audit.

```text
aligned raw tick count vs M1 tickvol corr 0.9816
placebo corr                         0.9863
aligned coverage                     99.77%
placebo coverage                     94.23%
joint coverage                       94.14%
bad bid/ask                               0
crossed quotes                            0
after-decision ticks                      0
```

This alignment/instrumentation is reusable for Slow-N.

### 4.3 Generic tick panel failed

Five original voters:

```text
NET, MOVE, MAG, CLV, RUN
```

NET and MAG are structurally duplicate in sign, so unique tick4 is:

```text
[NET, MOVE, CLV, RUN]
```

Generic tick direction remained around 50% and performed badly when overriding N2-R1 disagreement.

Conclusion: raw ticks are not a generic majority direction engine.

## 5. Strong Stoch/tick transition hypothesis

Let `D` = M5 Stochastic direction (`K>D => LONG`, otherwise SHORT).

Relative unique tick4 pattern:

```text
0001
NET  opposite D
MOVE opposite D
CLV  opposite D
RUN  same D
```

Prediction = D.

Performance:

```text
2024 N71 63.38%
2025 N64 68.75%
2026 N40 62.50%
ALL  N175 65.14%
```

Direction split pooled:

```text
LONG side  N79  70.89%
SHORT side N96  60.42%
```

Restricted symmetric family audit:

- 248 eligible chart/tick states after floors;
- candidate ranked #1 by minimum annual accuracy;
- within-family permutation empirical p ~0.0044.

This is strong development evidence for a mechanism candidate, not production authority.

Working interpretation:

```text
older/aggregate flow still points opposite D
latest raw quote run flips into D
M5 oscillator already points D
=> pullback-ending / re-synchronization state
```

### N2-R1 override diagnostic

On the special subset when Stoch/tick and N2-R1 disagreed:

```text
N73
Stoch/tick correct 60.27% (44/73)
N2-R1 correct      39.73% (29/73)
```

Two-sided binomial p was ~0.10, so this was not enough to declare a confirmed override.

A simple hybrid improved total direction accuracy only modestly (~+0.7pp overall), because the special subset was ~8% of events.

## 6. Bad-state / complement research

### Stoch relative `0000`

All four tick measures oppose Stoch. Following Stoch was only 45.61% pooled (N239); opposite Stoch 54.39%. Quarter behavior was unstable, so no inversion rule.

### Path Clearance relative `1110`

Path agrees NET/MOVE/CLV while RUN opposes Path. Following Path:

```text
2024 44.64% N112
2025 43.70% N119
2026 36.67% N60
ALL  42.61% N291
```

Opposite Path pooled 57.39%.

When Path disagreed with N2-R1 in this state, N2-R1 was much stronger, but this is post-hoc.

### M1 tape proxy relative `0000`

Following the chart-bar tape proxy was 41.28% pooled (N235), opposite 58.72%. This proxy is not true microstructure.

### Intersection: Stoch-new-flow versus Path-old-flow

Requiring Stoch relative `0001` and Path relative `1110` makes Stoch/RUN opposite Path/old-flow.

```text
N103
2024 Stoch/RUN 55.56%
2025 71.43%
2026 68.00%
ALL 65.05%
```

This strengthened the temporal-transition interpretation but remains nested/post-hoc.

## 7. M1 bridge research

M1 was identified as the missing timescale between M5 chart context and raw ticks.

Predefined causal M1 questions:

- recent 1/2/3m direction;
- candle pressure;
- confirmed swing structure;
- sweep/reclaim;
- Stoch 14,3,3;
- EMA3/EMA8 fast/slow;
- expansion context.

Standalone accuracy was near 50% for all; do not build an M1 indicator majority panel.

### M1 structure as N2 confidence state

When M1 confirmed structure agreed with N2-R1:

```text
N832
2024 60.07%
2025 60.12%
2026 59.15%
pooled 59.86%
```

When they disagreed, N2-R1 fell to 55.35% pooled.

### M1 recent price + Stoch/tick

Old Stoch/tick `0001`, plus M1 recent price direction still opposite D:

```text
N117
2024 66.04%
2025 70.00%
2026 62.50%
pooled 66.67%
```

Shifted-tick placebo pooled 38.18%.

### M1 Stoch alignment

Require M1 Stoch same direction as M5 Stoch D, plus tick `0001`:

```text
N57
2024 71.43%
2025 72.73%
2026 71.43%
pooled 71.93%
```

Shifted-tick placebo 47.12%.

Within-study constrained-family permutation p ~0.001; still not independent validation.

### M1 Stoch transition subset

M1 Stoch opposite M5 about three minutes earlier, now aligned, plus tick `0001`:

```text
N40
2024 76.92%
2025 70.59%
2026 80.00%
pooled 75.0%
```

Too small for promotion.

### Development trusted-state hierarchy

1. M1 structure agrees N2-R1 -> use N2-R1.
2. Otherwise if Stoch/tick `0001` -> use Stoch direction.
3. Otherwise unresolved.

```text
N905 / 42.11% coverage
2024 60.18%
2025 60.98%
2026 60.00%
pooled 60.44%
```

N2-R1 on same population was 59.12%.

Again: old population only.

## 8. Bollinger(20,2) state research

Bollinger was intentionally treated as a state/context representation rather than another binary voter.

Primary window = 5 prior completed M5 bars + N1 trigger bar. n=3 and n=8 used only for robustness.

Normalized SMA gap:

```text
gap = (close - SMA20) / (upper - SMA20)
upper band = +1
middle = 0
lower band = -1
```

Selected states:

### BB-A
Prior middle residence -> trigger near lower but still inside bands.

```text
DOWN N78 pooled 60.26%
2024 59.26 / 2025 64.00 / 2026 57.69%
```

Survived n=3/5/8 directionally.

### BB-B
Prior middle residence -> trigger closes above upper + absolute SMA distance path widens.

```text
UP N150 pooled 59.33%
2024 58.62 / 2025 60.42 / 2026 59.09%
```

Strongest cross-window upside archetype. Symmetric downside breakout did not work.

### BB-C
Trigger inside bands + normalized SMA gap shifts down + >=2 middle-line crosses.

```text
DOWN N71 pooled 63.38%
2024 64.29 / 2025 61.54 / 2026 64.71%
```

n=5-specific. When BB-C disagreed with N2-R1, BB-C was 72.73% on only N22; too small.

### BB-D
Prior middle residence + bandwidth contraction + exactly one middle-line cross.

```text
UP N160 pooled 61.25%
2024 60.00 / 2025 61.54 / 2026 62.50%
```

n=5-specific.

### Multiplicity

Primary n=5 scan: 749 eligible states, family-wise p ~0.268.
Cross-window analog scan p ~0.306.

Conclusion: Bollinger paths are useful hypotheses/context, not validated standalone edge.

## 9. What transfers to Slow-N

Transfer **definitions**, not percentages.

Priority preregistered hypotheses:

```text
H1: M5 Stoch D + tick relative 0001 predicts D
H2: H1 + M1 Stoch alignment improves reliability
H3: explicit M1 counter-move -> M1 oscillator resync -> last tick RUN flip is the causal sequence
H4: M1 confirmed structure can condition confidence
H5: Path relative 1110 identifies old-flow opposition
H6: BB-A/B/C/D describe contexts where direction authority may differ
```

Also transfer negative controls:

- generic 7-voter panel;
- generic tick majority;
- generic M1 majority;
- mechanical MTF expansion;
- exact small state pattern memorization.

## 10. Required Slow-N evaluation order

1. Freeze new Slow-N N1 first.
2. Join chart/M1/tick features by exact new decisions.
3. Re-run old fixed hypotheses unchanged before new discovery.
4. Include shifted placebo for tick-trigger claims.
5. Report year, quarter, direction-side and sample count.
6. Run near-miss and family-wise permutation audits.
7. If a previously strong mechanism fails, record failure; do not threshold-rescue it.
8. Only then open new Slow-N-specific discovery.
9. Do not use 2021.
