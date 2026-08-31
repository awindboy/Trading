# V8-A2 Final Reliability Layer — 2026-09-01

Status: `RESEARCH-ONLY SHADOW / IMPLEMENTATION READY / MT5 PARITY NOT YET CONFIRMED`

## Decision

Frozen V8-A remains the movement authority/control. V8-A2 is not allowed to silently replace it.

The A2 upgrade is finalized as a **three-layer information surface**:

```text
A2 survival P15/P30/P60
        +
trailing 288-completed-M5 percentile ranks R15/R30/R60
        +
relative movement state
```

State definition:

```text
EXTREME = R15,R30,R60 all >= 90
HIGH    = R15,R30,R60 all >= 75
QUIET   = R15,R30,R60 all <= 25
NORMAL  = otherwise
```

No direction is estimated.

## Why percentile rank is retained

The largest observed live-use risk is base-rate/calibration drift. The same fixed $10 move changed from rare in 2024 to common in 2026. Absolute probabilities therefore require caution.

Trailing relative rank preserved ordering much more consistently.

For factual V8 events, `HIGH` and `EXTREME` produced movement rates above the **same calendar month's full event base rate in all 32 evaluated months (2024-01 through 2026-08)** for P15, P30 and P60, subject to at least 10 state events in the month.

Monthly median lift:

| Horizon | HIGH | EXTREME |
|---|---:|---:|
| 15m | 2.80x | 4.16x |
| 30m | 2.58x | 3.61x |
| 60m | 2.11x | 2.69x |

## Annual EXTREME precision

| Year | P15 | P30 | P60 | Coverage |
|---|---:|---:|---:|---:|
| 2024 | 7.22% | 16.84% | 32.56% | 8.76% |
| 2025 | 24.81% | 41.06% | 60.31% | 8.40% |
| 2026 | 62.03% | 82.01% | 93.05% | 8.64% |

These percentages are **not portable guarantees**. Their absolute level changes with the movement base rate. The stable information is the relative lift/order.

Week-cluster bootstrap for `EXTREME - all-event movement rate` remained positive in all 9 year/horizon cells; see `extreme_week_cluster_bootstrap.csv`.

## Why automatic recalibration is not retained

Causal 180-day calibration/refit improved Brier in some later regimes but reduced or failed to improve ranking in other cells. It is therefore not part of the current live shadow contract.

The final information hierarchy is:

1. **rank/state** for regime-relative trust;
2. **raw A2 probability** as a secondary estimate;
3. frozen **V8-A** remains the control;
4. direction remains human/deterministic-entry responsibility.

## Implementation

### Indicator

`mt5/indicators/V8MovementProbabilityA2ReliabilityIndicator.mq5`

Buffers:

```text
0 P15 %
1 P30 %
2 P60 %
3 R15 percentile %
4 R30 percentile %
5 R60 percentile %
6 consensus rank = min(R15,R30,R60)
```

The status label does not use `Comment()` so it does not overwrite the frozen V8-A indicator comment.

Historical validated claims apply to factual V8 events. Continuous every-M5 output is context only.

### Parity

Compile the indicator, then run:

`mt5/scripts/V8A2ParityCheck.mq5`

The script checks 18 2024/2025/2026 historical references against the audited Python model pack.

Do not promote A2 if parity fails.

### Prospective logger

`mt5/experts/V8A2ProspectiveLoggerEA.mq5`

It logs only data observed prospectively after attachment and intentionally performs no historical backfill.

The frozen V8-A and A2 values are both recorded each completed M5. This ledger is the basis for later live calibration/ranking audits.

## Live interpretation

At a factual event:

- `EXTREME`: strongest relative movement state; direction still unknown.
- `HIGH`: movement likelihood materially elevated relative to recent market.
- `NORMAL`: no reliability upgrade.
- `QUIET`: relative suppression of movement, but do not interpret as guaranteed no-move in high-volatility regimes.

Do not interpret a displayed `90%` model probability as a guaranteed 90% realized frequency unless prospective calibration confirms it.

## Promotion gate

A2 may replace frozen A only after:

1. MQL parity passes;
2. prospective shadow ledger accumulates sufficient independent events;
3. recent score ordering remains monotonic;
4. calibration/Brier is defensible;
5. A2 continues to improve or at least preserve ranking versus A;
6. no change is made to GOLD# 2021 reserve before a separate decision.
