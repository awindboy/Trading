# V12 Phase-1H compact conviction head result

Date: `2026-09-24`

Status: `COMPLETE AND REPRODUCIBLE / COMPACT PATH PARTIAL / FROZEN PRIMARY GATE FAILED / NO ACTION AUTHORITY`

## Question

Can the useful Phase-1G information be reduced to a predeclared 50-field,
direction-symmetric competing-risk head that lowers stopped exposure while
preserving the right-tail capital required to size a journey? Do FAST/STD/SLOW
HA or Wave add information after that compact path is already known?

This is a consumed-development reassembly. It is not independent validation.
The contract, source fields, walk-forward folds, train-only conviction bands,
shadow allocation, and success gates were frozen before the Phase-1H models
were evaluated.

## Causal and reproducibility receipt

- Raw M1 rows revealed through `2026-09-18 23:57`: `1,669,073`.
- Post-cutoff price rows parsed: `0`; first unread row: `2026-09-21 01:00`.
- Actual V10 `ENTRY` Children: `1,409`; all have matched Wave rows.
- Primary compact head: `50` source fields: six structural categories, two
  structural numbers, ten continuous-clock coordinates, and eight path
  coordinates for each of four completed source-box families.
- The prior completed H4 FAST body reconstructed from raw M1 agrees with the
  retained Wave ledger to maximum absolute error `4.44e-16`.
- Two independently built nine-file packs are byte-identical. Five focused
  tests and complete-pack validation pass.

All score cut points come from each fold's training predictions. Test-fold
quintiles were never recomputed from test outcomes or test ranks.

## Out-of-time model result

Values are the unweighted mean of the three frozen expanding-window test
folds. Lower Brier/log loss and higher AUC are better.

| Model | Stop Brier | Stop log loss | Stop AUC | `>=5R` Brier | `>=5R` log loss | `>=5R` AUC |
|---|---:|---:|---:|---:|---:|---:|
| Continuous-clock control | 0.1199 | 0.3952 | 0.6625 | 0.0643 | 0.2516 | 0.6190 |
| Compact path | 0.1082 | 0.3626 | 0.7100 | **0.0634** | **0.2443** | **0.6564** |
| Compact path + HA | **0.1061** | **0.3539** | **0.7413** | 0.0634 | 0.2446 | 0.6519 |
| Compact path + Wave | 0.1085 | 0.3681 | 0.7245 | 0.0634 | 0.2443 | 0.6473 |
| Compact path + HA + Wave | 0.1075 | 0.3640 | 0.7403 | 0.0635 | 0.2444 | 0.6499 |

The compact path beats the continuous-clock control for both heads on mean log
loss and in at least two folds. HA improves the stop log loss in all three
folds (`-0.0094`, `-0.0092`, `-0.0075` versus compact path), but slightly
worsens mean right-tail log loss by `0.00025`. Wave worsens mean stop log loss
by `0.00557`, including a `+0.03066` deterioration in fold 2. Neither HA nor
Wave passes the predeclared two-head incremental gate.

## Capital result

The compact model's highest train-calibrated conviction band reduces stopped
exposure in every fold:

| Fold | Population stop/100 | Q5 stop/100 | Population R/unit | Q5 R/unit | Q5 funded units |
|---|---:|---:|---:|---:|---:|
| F1 | 11.84 | **1.19** | 0.127 | **0.287** | 253 |
| F2 | 14.11 | **4.71** | **0.272** | 0.252 | 297 |
| F3 | 13.61 | **6.93** | 0.117 | **0.159** | 101 |
| Pooled | 13.21 | **3.69** | 0.183 | **0.251** | 651 |

The frozen primary gate fails because fold-2 Q5 earns slightly less R per unit
than its population, even though it stays positive and removes about two thirds
of stopped exposure. The non-veto shadow tilt (`0.75x/1x/1.25x`) lowers pooled
stopped units from `13.21` to `12.11` per 100, retains `97.8%` of baseline
R/unit, and retains `92.0%` of right-tail units per funded unit. Those capital
gates pass, but they do not override the failed Q5 fold gate.

HA exposes the most useful component split. Its Q5 has only `22` stopped units
over `647` funded units (`3.40 / 100`) and positive R/unit in all folds
(`0.300`, `0.306`, `0.172`). It passes every frozen capital gate. It still fails
promotion because HA improves stop discrimination, not right-tail prediction.
Using one identical feature set for both competing outcomes is therefore not
the best supported assembly.

## Stability and normalization limits

- Compact Q5 lowers stopped exposure and remains positive for both LONG and
  SHORT. SHORT Q5, however, contains no `>=5R` units; side stability of the
  right tail is not established.
- Every test observation falls in the highest tercile defined by its historical
  training window's absolute prior-60-day daily range. This is direct evidence
  of liquidity-era drift. The contracted eligible-cell test passes only for T3;
  it does not establish low/mid-era coverage.
- This supports normalized path coordinates, but rejects treating an absolute
  historical-volatility bucket as a stable regime label.

## Decision

Phase 1H does not authorize a veto or position-size map. The primary compact
head and all HA/Wave variants fail their frozen overall gates.

The retained structural finding is narrower and more useful:

1. continuous settlement, repair, and boundary-consumption state jointly
   carries stop and right-tail information;
2. FAST/STD/SLOW HA disagreement adds incremental stop information after path
   state, but not incremental right-tail information;
3. the retained Wave summary does not add robust information after path and HA;
4. the next frozen model should use asymmetric component roles: HA may enter the
   stop head while the right-tail head remains path-led, with calibration and
   capital preservation judged jointly;
5. that assembly is a consumed-data hypothesis and must be frozen before any
   unread chronology is opened.

All observations through `2026-09-18 23:57` remain consumed development
evidence. GOLD# 2021 and post-cutoff chronology remain sealed. Phase 1H has no
trade, veto, exit, retry, sizing, EA, or production authority.
