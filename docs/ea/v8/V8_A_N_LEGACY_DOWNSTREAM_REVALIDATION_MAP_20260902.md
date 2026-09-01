# V8-A-N Legacy Downstream Revalidation Map — Slow-N Transfer Status — 2026-09-02

Status: `ACTIVE TRANSFER AUDIT / DEVELOPMENT ONLY`
Old source population: `1.50 * M5 ATR fresh75`
New population: `0.25 * previous-completed H4 ATR fresh75 probe`
Reserve: `GOLD# 2021 untouched`

## 1. Transfer rule

Transfer **definitions and falsification methods**, not old percentages.

A legacy result can only become relevant to Slow-N after its definition is applied to the new Slow-N event population without outcome-driven redesign.

The probability probe itself has two outcome-blind training realizations, Phase-0 and Phase-2. Strong downstream candidates should survive both where feasible.

## 2. Completed negative-control transfer

| Legacy method | Slow-N evidence | Status |
|---|---|---|
| deterministic 7-voter | P0 51.73/54.08/50.00; P2 49.17/56.79/49.83 | FAIL |
| M5 Stoch standalone | P0 47.96/51.99/54.46; P2 46.25/53.79/51.92 | FAIL |
| market-question equal panel | 50.94/53.51/48.41 | FAIL |
| immediate pressure | 49.69/51.80/47.45 | FAIL |
| oscillator transition | 50.00/52.18/51.59 | FAIL |
| M15 structure | 50.94/53.51/54.14 | FAIL |
| H1 structure | 48.27/52.75/53.18 | FAIL |
| H4 structure | 51.10/52.37/52.87 | FAIL |
| HTF regime | 52.04/49.72/54.14 | FAIL |
| volatility transition | 50.63/54.08/50.00 | FAIL |
| location/liquidity | 49.06/52.18/50.00 | FAIL |
| M1 tape proxy | 50.16/53.51/50.32 | FAIL |
| M1 recent direction | 48.90/51.99/50.00 | FAIL |
| M1 pressure | 51.10/53.32/53.18 | FAIL |
| M1 Stoch | 51.10/47.63/51.59 | FAIL |
| M1 EMA3/8 | 51.89/52.94/48.41 | FAIL |
| old asymmetric MTF state | UP 36.36/50.00/63.64 | FAIL / reversal |
| generic tick majority on overlap | 50.86/52.32/52.17 | FAIL |

These methods should not receive threshold/weight rescue.

## 3. Bollinger state transfer

The exact legacy semantic state definitions were reused.

### BB-A

```text
prior middle residence
trigger near lower but inside
predict DOWN
```

Phase-0 n=5:

```text
50.00 / 55.56 / 58.33%
```

Status: `FAIL`.

### BB-B

```text
prior middle residence
trigger closes above upper band
absolute normalized SMA-distance path AWAY
predict UP
```

Phase-0 n=5:

```text
2024 N34 58.82%
2025 N17 76.47%
2026 N13 69.23%
pooled N64 65.63%
```

Phase-2 n=5:

```text
2024 N34 64.71%
2025 N18 66.67%
2026 N11 63.64%
pooled N63 65.08%
```

Window robustness:

```text
Phase-0 n3: 55.56 / 70.00 / 57.14
Phase-0 n5: 58.82 / 76.47 / 69.23
Phase-0 n8: 66.67 / 71.43 / 62.50

Phase-2 n3: 55.17 / 61.54 / 58.33
Phase-2 n5: 64.71 / 66.67 / 63.64
Phase-2 n8: 71.43 / 60.00 / 71.43
```

All 18 year x phase x window cells are above 50%.

Status: `RETAIN / STRONG DEVELOPMENT CANDIDATE / NOT VALIDATED`.

### BB-C

Phase-0:

```text
DOWN 57.14 / 61.90 / 33.33%
```

Status: `FAIL / 2026 relation reversal`.

### BB-D

Phase-0:

```text
UP 52.94 / 52.63 / 54.17%
```

Status: `FAIL`.

## 4. Raw-tick transfer limitation

V4 raw ticks were instrumented only for the legacy M5-A-N N1 events.

Therefore no claim has yet been made on the full new Slow-N population.

New/old resolved overlap:

```text
N418
```

Generic tick majority:

```text
2024 50.86%
2025 52.32%
2026 52.17%
pooled 51.67%
```

Status: `FAIL`.

### Predefined Stoch-relative 0001

Let D = M5 Stoch direction.

```text
NET  opposite D
MOVE opposite D
CLV  opposite D
RUN  same D
predict D
```

Aligned overlap:

```text
2024 N18 61.11%
2025 N20 70.00%
2026 N7  71.43%
ALL  N45 66.67%
```

-10m shifted placebo:

```text
ALL N40 45.00%
```

Nested M1 observations:

```text
M1 recent counter-move                       N26 65.38%
M1 Stoch aligned                             N14 85.71%
M1 Stoch 3m opposite -> now aligned          N10 90.00%
```

Status: `RETAIN AS MECHANISM HYPOTHESIS ONLY`.

Reason: coverage is inherited from the legacy tick ledger and sample sizes are small. Full Slow-N tick extraction is mandatory.

## 5. M1 reproducibility issue

Legacy M1 standalone states such as Stoch/pressure/EMA could be reproduced exactly enough for transfer tests and remained negative.

The confirmed-swing `M1 structure` generator could not be recovered exactly from the retained artifacts; reconstruction reached only ~85% state parity.

Status:

```text
M1 confirmed structure transfer = BLOCKED
```

Do not use old `M1 structure == N2-R1` percentages as new evidence.

## 6. Current mechanism picture

The current useful hypotheses are not generic voting.

### Context layer

```text
BB-B
middle residence
-> upper escape
-> SMA-distance expansion
```

### Transition layer

```text
M5 Stoch D
while older raw flow remains opposite
-> M1 oscillator aligns D
-> last tick RUN flips D
```

A future integrated hypothesis may ask whether BB-B identifies the environment in which temporal re-synchronization is most reliable.

Do not open arbitrary combination search before full tick coverage.

## 7. Next transfer tasks

1. raw ticks for all new Slow-N events;
2. aligned vs -10m placebo;
3. full `0001` transfer;
4. M1 Stoch alignment/transition;
5. native Slow-N Path Clearance;
6. BB-B x temporal transition;
7. recover/freeze confirmed M1 structure;
8. near-miss and family-wise permutation audit;
9. only then new feature discovery.
