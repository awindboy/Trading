# V10 Intrabar Next-HA Nowcast Checkpoint

Date: `2026-09-21`
Status: `CONSUMED-DATA DIAGNOSTIC / STANDALONE EXIT AUTHORITY REJECTED`
Market: `GOLD# ONLY`
Base GitHub `main`: `438f6b4d588330b4cd2f1cae7cba968f14df36e4`

## 1. Question

Can the raw-M1/M5 path inside a **forming next H4 bar** predict whether that bar
will finish as campaign-direction PHA or opposite-direction NHA early enough to
reduce repeated Child Hard SLs?

This differs from the earlier completed-bar next-HA work.  The target H4 has
already begun, and only its causal prefix is observed.

## 2. Fixed experiment contract

Source lineage:

```text
raw M1 SHA256
626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2

R3 causal universe SHA256
f352a99c746752ca259da33dbdaee9d8f0cb874bd01cf520a487fe1bdbf82609

MT5 R7G event export SHA256
c4348a34aa35d1e9793283cebbf1a028327c10e3e1c5a4fde2a9e74e3ff801a7
```

Observation points:

```text
forming H4 +60 minutes
forming H4 +120 minutes
forming H4 +180 minutes
```

At each point, only M1 rows strictly before the checkpoint are used.  FAST HA
open and the Wilder H4 ATR180 normalization scale come from completed prior H4
bars.  The final target H4 color is label-only.

Compact representation:

```text
normalized provisional FAST-HA margin
prefix return / range / favorable and adverse excursion
directional path efficiency / favorable-extreme retracement
last 15 / 30 / 60 minute return
completed M5 alignment / transitions / signed streak / body efficiency
prefix coverage
```

Fixed model:

```text
RobustScaler(10, 90)
+ LogisticRegression(C=1.0)
```

Outer-year rule:

```text
2024 <- labels available before 2024
2025 <- labels available before 2025
2026 <- labels available before 2026
```

No model-family, C, checkpoint or threshold scan was used.  The only
model-action diagnostic is `p_NHA >= prior-training score q90`.

Economic action:

```text
close the newest Child only
at the exact checkpoint M1 open
only if the Child is still alive
```

Older campaign Children remain unchanged.  A Child stopped before the warning
is dead and cannot be rescued.

## 3. Population and parity

```text
R3 causal opportunities                  6,770
prefix rows                             19,446
matched R7G selected Children            1,649
scored selected checkpoint rows          4,727
rebuilt next-HA label mismatches              0
selected direction mismatches                0
selected k mismatches                        0
```

The MT5 export contains 66 later or unresolved positive-weight rows outside the
resolved frozen universe.  They are not backfilled.

The +60-minute population is 1,429 rather than 1,649 because 220 target H4 bars
do not expose a usable first-hour prefix under the raw-M1/market-hours clock.

## 4. Next-HA classification result

Outer-year pooled result:

| Checkpoint | NHA rate | Provisional HA margin AUC | Compact path-model AUC | Prior-q90 precision | Prior-q90 recall |
|---:|---:|---:|---:|---:|---:|
| +60m | 21.55% | 0.8791 | 0.8769 | 89.11% | 29.22% |
| +120m | 22.20% | 0.9230 | 0.9217 | 94.40% | 32.24% |
| +180m | 22.20% | 0.9605 | 0.9601 | 97.71% | 34.97% |

The forming H4 final color is highly predictable as the bar matures.  However,
the M1/M5 path model adds essentially no stable discrimination beyond the
normalized provisional FAST-HA margin itself.

Interpretation:

```text
most observed predictability
= observing the same O/H/L/C components
  that mathematically determine FAST HA color

not

a newly discovered LTF directional oracle
```

## 5. Economic conversion

R7G-weighted newest-Child simulation:

| Policy | Executed early exits | Hard SLs prevented | Baseline R | Policy R | Delta R | L6+ positive-R retention |
|---|---:|---:|---:|---:|---:|---:|
| Provisional NHA at +60m | 211 | 64 | 706.88 | 645.53 | -61.35 | 91.94% |
| Prior-q90 model at +60m | 73 | 25 | 706.88 | 704.91 | -1.97 | 99.06% |
| Prior-q90 model at +120m | 72 | 17 | 741.01 | 718.50 | -22.51 | 98.35% |
| Prior-q90 model at +180m | 58 | 8 | 741.01 | 728.36 | -12.65 | 99.17% |
| Earliest prior-q90 warning | 128 | 39 | 741.01 | 712.62 | -28.39 | 97.58% |
| Perfect NHA oracle at +60m | 280 | 91 | 706.88 | 955.10 | +248.22 | 99.91% |

The earliest model warning reduced Hard SL count from `232` to `193`, but the
maximum consecutive Hard-SL streak stayed `5`.  It did not achieve the user's
primary objective of compressing repeated stops.

The perfect +60-minute NHA oracle reduced the comparable maximum stop streak
from `4` to `2`.  Therefore useful theoretical room exists, but the tested
causal classifier did not capture it economically.

## 6. Why high precision still lost R

For executed +60-minute prior-q90 warnings:

```text
64 true-NHA exits       +18.42R versus holding
 9 false-PHA exits      -20.38R versus holding
----------------------------------------------
total                    -1.97R
```

The problem is not ordinary classification accuracy.  The remaining false
positives are economically asymmetric: a few PHA errors cut right-tail winners
whose cost exceeds the losses saved on correctly identified NHA bars.

Later checkpoints have higher color accuracy but less remaining loss to save.
At +180 minutes, true-NHA q90 exits added only `+0.59R`, while two false-PHA
exits cost `-13.24R`.

## 7. Research decision

Supported:

```text
forming-H4 NHA nowcasting is technically feasible
provisional FAST-HA margin is the dominant compact coordinate
there is a large perfect-information ceiling at +60 minutes
```

Rejected:

```text
standalone intrabar NHA prediction as early-exit authority
M1/M5 feature expansion as evidence of a new oracle
accuracy / AUC as sufficient justification for Child exit
```

The next valid question is not merely `will this H4 finish NHA?`.  It is:

```text
given the current Child risk and open profit/loss,
is exiting now better than preserving the remaining right tail?
```

That is an asymmetric action-value question, not another direction or regime
classifier.  It must be frozen as a separate future shadow contract before any
action authority is considered.

## 8. Reproducibility

Code:

`research/v10/analyze_v10_intrah4_next_ha_nowcast.py`

Generated local ledgers (removed during the 2026-09-21 repository cleanup; rerun the retained script to regenerate):

```text
output/v10_intrah4_nowcast_20260921/V10_INTRAH4_NOWCAST_MANIFEST.json
output/v10_intrah4_nowcast_20260921/V10_INTRAH4_NOWCAST_PREFIX_LEDGER.csv
output/v10_intrah4_nowcast_20260921/V10_INTRAH4_NOWCAST_SCORED_SELECTED.csv
output/v10_intrah4_nowcast_20260921/V10_INTRAH4_NOWCAST_CLASSIFICATION.csv
output/v10_intrah4_nowcast_20260921/V10_INTRAH4_NOWCAST_CLASSIFICATION_POOLED.csv
output/v10_intrah4_nowcast_20260921/V10_INTRAH4_NOWCAST_POLICY.csv
output/v10_intrah4_nowcast_20260921/V10_INTRAH4_NOWCAST_Q90_DECOMPOSITION.csv
```

All 2022-2026 observations remain consumed development evidence.  This
checkpoint does not modify current V10 strategy, R7G sizing, EA behavior, or
production authority.
