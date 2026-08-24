# D-154O Stage B 2025 Results

Status: `COMPLETE / OUTCOME B / NO STRATEGY AUTHORITY`  
Date: `2026-08-24`  
Execution environment: `XM Ultra Low`  
EA: `2.11R0L11 / D154M`  
Stage-B model: `Every tick based on real ticks`  
Period: `2025-01-01 .. 2025-12-31`

## Frozen cohort integrity

The Stage-B cohort was frozen before new 2025 outcomes:

```text
REFERENCE
GOLD#

GOLD_LIKE
XAUJPY#
XAUCNH#
BTCUSD#
XAUEUR#
GAUCNH#
GAUUSD#
USDJPY#

NEGATIVE_CONTROL
GBPUSD#
SILVER#
EURUSD#
ETHUSD#
```

No symbol was added or removed after outcome visibility.

## Infrastructure / execution integrity

Eleven symbols have clean D151/D154K/D154M population integrity.

`GBPUSD#` is **execution-invalid for profitability / survival inference** in this run.

Sequence:

```text
2025-01-31 20:20:00
pending order accepted

2025-02-03 00:00:03
scenario canceled because objective was delivered
-> pending cancel attempted
-> broker rejected cancel: Market closed
-> order may survive

2025-02-04 17:02:21
surviving broker order filled
-> execution_status=EXECUTION_DIVERGENCE
-> divergence=true
```

The frozen control remains in the manifest but its 42.3% raw survival is not canonical evidence.
Do not replace it with another control after outcome visibility.

## Primary Stage-B results

| Symbol | Cohort | Fills | Fill->+1R | LONG | SHORT | exact spread/reactionTR | spread/1R | spread/selected FVG | D154M shadow | SL->shadow +1R |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GOLD# | REFERENCE | 55 | 58.2% | 64.7% | 47.6% | 0.162 | 0.014 | 0.247 | 58.2% | 0 |
| XAUJPY# | GOLD_LIKE / INSUFFICIENT | 14 | 42.9% | 37.5% | 50.0% | 0.248 | 0.020 | 0.410 | 42.9% | 0 |
| XAUCNH# | GOLD_LIKE / INSUFFICIENT | 12 | 50.0% | 50.0% | N/A | 0.277 | 0.025 | 0.383 | 58.3% | 1 |
| BTCUSD# | GOLD_LIKE | 127 | 48.8% | 47.5% | 50.0% | 0.541 | 0.032 | 0.550 | 51.2% | 3 |
| XAUEUR# | GOLD_LIKE | 58 | 48.3% | 50.0% | 46.7% | 0.347 | 0.035 | 0.608 | 50.0% | 1 |
| GAUCNH# | GOLD_LIKE / INSUFFICIENT | 14 | 57.1% | 57.1% | N/A | 0.406 | 0.032 | 0.586 | 64.3% | 1 |
| GAUUSD# | GOLD_LIKE / INSUFFICIENT | 10 | 70.0% | 85.7% | 33.3% | 0.518 | 0.039 | 0.883 | 70.0% | 0 |
| USDJPY# | GOLD_LIKE | 94 | 47.9% | 52.1% | 43.5% | 0.390 | 0.028 | 0.480 | 50.0% | 2 |
| GBPUSD# | CONTROL / EXECUTION_INVALID | 111 | NOT EVIDENCE | NOT EVIDENCE | NOT EVIDENCE | 0.692 | 0.056 | 1.000 | NOT EVIDENCE | 7 |
| SILVER# | CONTROL | 47 | 38.3% | 41.4% | 33.3% | 1.302 | 0.108 | 1.500 | 38.3% | 0 |
| EURUSD# | CONTROL | 95 | 42.1% | 39.2% | 45.5% | 0.692 | 0.049 | 0.857 | 45.3% | 3 |
| ETHUSD# | CONTROL | 72 | 38.0%* | 37.5% | 38.7% | 1.037 | 0.052 | 1.367 | 38.0% | 0 |

`* ETHUSD#`: 27 PLUS_1R, 44 SL_FIRST, 1 RIGHT_CENSORED; resolved denominator = 71.

The pre-registered `<20 fills` descriptive guard marks
`XAUJPY#`, `XAUCNH#`, `GAUCNH#`, and `GAUUSD#` as
`INSUFFICIENT_STRATEGY_SAMPLE`. Their high/low WR values are not promotion evidence.

## Stage-A proxy validation

Stage A did succeed at identifying execution scale.

Across the frozen 12-symbol panel:

```text
Spearman(
  Stage-A raw spread/M1-TR,
  Stage-B exact D154K spread/reactionTR
) ~= +0.888

Spearman(
  Stage-A raw spread/generic-FVG,
  Stage-B exact spread/selected-causal-FVG
) ~= +0.874
```

More importantly, exact Stage-B `spread/reactionTR` preserves a clean friction block:

```text
GOLD#       0.162
XAUJPY#     0.248
XAUCNH#     0.277
XAUEUR#     0.347
USDJPY#     0.390
GAUCNH#     0.406
GAUUSD#     0.518
BTCUSD#     0.541
-----------------
GBPUSD#     0.692  execution-invalid
EURUSD#     0.692
ETHUSD#     1.037
SILVER#     1.302
```

Therefore the one-week raw screen is a useful **market-level execution proxy**.
It is not exact D154K and it is not a per-trade Entry threshold.

## Survival interpretation

The sufficiently sampled Gold-like new-validation markets did not reproduce GOLD#'s 58.2%:

```text
BTCUSD#   48.8%
XAUEUR#   48.3%
USDJPY#   47.9%
```

Valid controls:

```text
EURUSD#   42.1%
SILVER#   38.3%
ETHUSD#   38.0%
```

Descriptive pooled comparison, excluding the execution-invalid GBPUSD#:

```text
sufficient-sample Gold-like candidates
BTCUSD# + XAUEUR# + USDJPY#
= 135 / 279
= 48.4%

valid controls
SILVER# + EURUSD# + ETHUSD#
= 85 / 213
= 39.9%

difference
= +8.5 percentage points
```

This pooled number is descriptive only. Markets are not independent Bernoulli replicas,
and the GOLD-family instruments are especially correlated.

Direction-preserved pooled comparison:

```text
Gold-like sufficient-sample candidates
LONG   68 / 137 = 49.6%
SHORT  67 / 142 = 47.2%

valid controls
LONG   47 / 120 = 39.2%
SHORT  38 / 93  = 40.9%
```

The relative advantage is therefore not only a LONG/SHORT composition artifact.

## D154M interpretation

Quote-side friction remains causal but partial.

Low-friction sufficient-sample markets:

```text
GOLD#       0 flips
BTCUSD#     3
XAUEUR#     1
USDJPY#     2
```

Controls:

```text
SILVER#     0
EURUSD#     3
ETHUSD#     0
GBPUSD#     7  (execution-invalid run)
```

`SILVER#` and `ETHUSD#` have poor Entry survival despite zero D154M rescue flips.
This again rejects execution spread as a universal explanation.

## Reproducibility check

The new Stage-B run reproduced the prior D154UL 2025 core values:

```text
GOLD#      survival 58.2%, spread/reactionTR ~0.162
BTCUSD#    survival 48.8%, spread/reactionTR ~0.541
SILVER#    survival 38.3%, spread/reactionTR ~1.302
```

This supports batch consistency.

## V3E / exit-execution caveat

D154O's primary question is Entry survival, not exit optimization.

Exact aggregate V3E cost-adjusted WR / average-winner-R / expectancy-R is not reconstructed
from the event CSV because mode 9 can realize partial-close deals whose complete realized
deal P/L and fees are not contained in the terminal `POSITION_CLOSED` row.

Do not fabricate these metrics.

Additional execution observations are retained for the later exit/execution stage:

```text
D149 partial-close requests rejected while market closed:
SILVER#   1823 retries
XAUEUR#     82 retries
EURUSD#     47 retries
USDJPY#      6 retries
```

These retries do not invalidate Fill->+1R evidence. They are post-+1R / exit-execution facts
and must remain separate from Entry research.

## D154O decision

Frozen contract outcome:

```text
OUTCOME B
```

Interpretation:

```text
execution suitability is supported
+
Stage-A raw screen is useful for identifying it
+
low friction is associated with materially better Entry survival
BUT
low friction is not sufficient to reproduce GOLD-like survival
and does not by itself satisfy the >=50% baseline objective
```

Therefore:

- do not create a production market-eligibility layer from D154O;
- do not fit a per-trade spread threshold;
- do not add/drop symbols using 2025 outcome;
- do not force high-friction markets back into primary research;
- retain the low-friction cohort as the preferred environment for the next Entry-mechanism study;
- move next to low-friction **pre-Fill regime/path-quality** research;
- keep D154N deferred unless later evidence specifically requires the pending-to-Fill mechanism.

No Entry, SL, TP, sizing, SP, EM, or baseline strategy change is authorized.
