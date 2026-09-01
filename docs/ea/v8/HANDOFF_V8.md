# V8 Development Handoff

Last updated: `2026-09-01`
Current phase: `V8-A-N N1 FROZEN / N2 NEW-INFORMATION DIRECTION RESEARCH`
Production authority: `NONE`
Market: `GOLD#`
Untouched reserve: `GOLD# 2021`

## 1. Read-this-first

The normalized movement research succeeded at the **movement/trigger** layer but not yet at the complete trading layer.

Current primary chain:

```text
V8-A-N movement surface
        ↓
N1 = 1.50ATR fresh P15 75-cross FROZEN
        ↓
N2 direction = current bottleneck
        ↓
N3 ATR exits paused until N2 improves
```

Fixed-$10 fresh75 with $10 SL / $13 TP remains the stronger complete development benchmark.

## 2. N1 frozen trigger

```text
ATR = causal pre-decision M5 Wilder ATR14
barrier = 1.50 ATR

previous P15_1.50ATR <75%
current P15_1.50ATR >=75%
```

Direction-blind selection.

Movement realization:

```text
2024 N809 P15 81.64% P30 93.92% P60 98.88%
2025 N834 P15 77.85% P30 91.77% P60 98.18%
2026 N551 P15 80.04% P30 93.77% P60 97.80%
```

Monthly count is roughly 67-70, active-day median 3, median trigger spacing roughly 5.5-6.3 hours.

Do not change k because of later direction results.

## 3. N2 result

First 2024-only technical rule:

```text
2024 ~59.6%
2025 48.28%
2026 49.44%
```

Falsified. No threshold rescue.

After all years became development evidence, N2-R1 maximin ensemble produced:

```text
2024 57.34%
2025 57.62%
2026 57.43%
```

This is stable but post-hoc and has no independent-validation authority.

Broad chronological regularized models did not improve transfer.

Interpretation:

`direction remains the bottleneck`.

## 4. N3 result

With N2-R1:

```text
SL1 / TP1 ATR:
WR ~55%, EV ~+0.09 to +0.11R
but winner =1R

SL1 / TP1.25:
WR 49.94 / 49.04 / 51.18%
EV +0.124 / +0.103 / +0.153R

SL1 / TP1.50:
WR 45.36 / 46.16 / 47.55%
EV +0.134 / +0.150 / +0.191R
```

None meet the combined project requirement across all years.

One-position sensitivity is nearly identical because most signals resolve quickly.

Do not fine-tune nearby TP values yet.

## 5. Cost warning

A 1ATR stop is small relative to recorded spread in 2024:

```text
median entry spread / 1ATR risk:
2024 ~13.7%
2025 ~6.1%
2026 ~4.9%
```

These are rough M1 spread proxies, not exact MT5 costs.

Real-tick execution is mandatory before any normalized strategy authority.

## 6. Benchmark

Existing fixed-$10 fresh75 development benchmark:

```text
SL $10 / TP $13

2025 WR52.63% EV+0.207R
2026 WR52.07% EV+0.198R
```

Current normalized complete candidate is inferior to this benchmark despite having a much better movement target/cadence.

Do not confuse a superior movement model with a superior complete trade.

## 7. Next research

Keep N1 fixed.

Next work:

1. construct frozen-N1 tick/quote probe;
2. extract trigger-local 5s/15s/30s/60s/180s/300s raw quote features;
3. include shifted placebo windows;
4. test whether tick information improves direction above N2-R1;
5. do not reopen N3 unless direction improves materially;
6. if XM quote information also fails, consider CME GC order flow / macro surprise;
7. keep 2021 locked.

## 8. Other branches

V8-A/A2 remain unchanged.

V8-C LONG remains provisionally frozen and real-tick verified; do not modify its entry.

V8-C-S1 remains research-only.

V8-C exit/winner-continuation work remains retained but is not the immediate priority.
