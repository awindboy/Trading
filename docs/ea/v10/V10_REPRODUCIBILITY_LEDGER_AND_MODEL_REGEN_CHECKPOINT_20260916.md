# V10 Reproducibility Ledger and Model-Regeneration Checkpoint

Date: `2026-09-16`  
Status: `REPRODUCIBILITY / DATA-LINEAGE CHECKPOINT / SHADOW RESEARCH / NOT PRODUCTION AUTHORITY`  
Market: `GOLD# ONLY`  
Package base GitHub main HEAD: `f5bd80136b152a2508213c6d8ef77642062a4ebe`  
Production authority: `NONE`  
EA authority: `RESEARCH / DEMO ONLY`

## 1. Why this checkpoint exists

The previous V10 update correctly preserved the post-HEAD research conclusions and the first actual-tick execution defect. The remaining weakness was **row-level reproducibility**.

Several useful post-HEAD results had survived only as session-recorded statistics. In particular, the recorded `bounded m3 + extreme NHA-shock veto` result did not retain its exact fitted coefficient vector, preprocessing state, per-event scores, or veto-row ledger. Therefore it must not be reconstructed by guessing.

This checkpoint changes the research standard from:

```text
"the summary number is written down"
```

to:

```text
raw evidence
-> exact row ledger
-> causal feature ledger
-> deterministic preprocessing
-> saved coefficients
-> per-event score ledger
-> prior-only percentile reference
-> economic decision ledger
-> validation receipt
```

A research claim is not implementation-ready unless this chain can be inspected.

## 2. What is now persisted

### 2.1 Raw actual-tick evidence

The exact files used for the first bounded-m3 MT5 diagnostic are preserved under:

```text
docs/ea/v10/results/raw/
```

- `V10_BOUNDED_M3_ACTUAL_TICK_EVENTS_RAW_20260916.csv`
- `V10_BOUNDED_M3_ACTUAL_TICK_REPORT_RAW_20260916.xlsx`

Their SHA256 values are fixed in `V10_DATA_AND_LEDGER_MANIFEST_20260916.md` and in the validation script.

### 2.2 Signal-level execution ledger

`V10_BOUNDED_M3_ACTUAL_TICK_SIGNAL_EXECUTION_LEDGER_20260916.csv`

One row per selected bounded-m3 signal:

```text
1,159 rows
```

The ledger links the selected decision to:

- exact decision timestamp;
- side and units;
- structural SL;
- entry fill / market-closed reject / SL-already-touched reject;
- actual entry time and price;
- actual exit time and price;
- actual PnL;
- actual exit reason;
- intended FAST-NHA exit timestamp where reconstructable;
- whether the position was affected by a rejected NHA close.

This is the canonical bridge from the research signal population to the first Strategy Tester execution.

### 2.3 Entry-reject ledger

`V10_BOUNDED_M3_ACTUAL_TICK_ENTRY_REJECT_LEDGER_20260916.csv`

```text
175 rows
= 174 market-closed entry rejects
+ 1 structural fail-closed SL-already-touched reject
```

Do not silently impute fills for these rows in the exact-timestamp control.

### 2.4 Exit-reject evidence

The exit defect is now retained at three levels.

```text
V10_BOUNDED_M3_ACTUAL_TICK_EXIT_REJECT_EVENT_LEDGER_20260916.csv
-> 134 individual rejected close requests

V10_BOUNDED_M3_ACTUAL_TICK_EXIT_REJECT_INCIDENT_LEDGER_20260916.csv
-> 84 distinct reject timestamps / incidents

V10_BOUNDED_M3_ACTUAL_TICK_EXIT_REJECT_AFFECTED_LEDGER_20260916.csv
-> 131 filled positions materially affected
```

This prevents the actual-tick defect from being reduced to a prose note.

### 2.5 Pending-exit delay ledger

`V10_BOUNDED_M3_ACTUAL_TICK_PENDING_EXIT_DELAY_LEDGER_20260916.csv`

```text
131 rows
```

For each contaminated filled Child it records:

```text
intended FAST-NHA exit
actual exit
unintended additional holding time
entry / SL / exit prices
actual PnL and exit reason
```

This ledger is the main reference when validating the corrected immutable `EXIT_PENDING` implementation.

### 2.6 Exposure path and overlap episodes

```text
V10_BOUNDED_M3_ACTUAL_TICK_EXPOSURE_PATH_LEDGER_20260916.csv
-> 1,968 deal-state rows

V10_BOUNDED_M3_ACTUAL_TICK_OVERLAP_EPISODE_LEDGER_20260916.csv
-> 33 opposite-direction overlap episodes
```

The first defective tick run reached:

```text
max gross exposure = 16 units
opposite-direction overlap ~= 311.0125 hours
```

These are execution-fidelity diagnostics, not desired policy behavior.

### 2.7 Deal and order ledgers

```text
V10_BOUNDED_M3_ACTUAL_TICK_DEALS_LEDGER_20260916.csv
-> 1,968 rows

V10_BOUNDED_M3_ACTUAL_TICK_ORDERS_LEDGER_20260916.csv
-> 1,968 rows
```

They retain the normalized MT5 Tester rows used to reconstruct entries, exits, PnL and exposure.

### 2.8 Structural-SL execution ledger

`V10_BOUNDED_M3_ACTUAL_TICK_SL_EXECUTION_LEDGER_20260916.csv`

```text
252 structural-stop positions
```

It preserves intended structural risk geometry versus actual gap/slippage execution. It should be used for tail-risk study; it does not redefine the structural SL itself.

### 2.9 Causal selected-signal MTF feature ledger

`V10_POST_HEAD_SELECTED_SIGNAL_FEATURE_LEDGER_20260916.csv`

```text
1,159 rows
62 columns
```

The causal feature set was rebuilt from authoritative uploaded M15 / M30 / H1 / H4 OHLC data and the selected-signal timestamps.

The ledger contains compact semantic state rather than an arbitrary indicator soup, including:

- H4 FAST HA current state and signed body geometry;
- M15 FAST HA internal delivery over completed bars;
- M30 FAST HA internal delivery over completed bars;
- H1 standard HA internal delivery over completed bars;
- aligned fraction;
- transition rate;
- current signed streak;
- longest aligned/opposed streaks;
- signed HA body-flow coordinates;
- opposing-wick share;
- previous-completed H4 ATR180 coordinate.

Direction parity against all 1,159 selected signals is:

```text
0 mismatches
```

## 3. Causal boundary of the feature ledger

At a decision timestamp, only lower-timeframe bars completed before that timestamp are used.

The following columns are explicitly **answer-sheet only**:

```text
answer_final_run_len
answer_future_remaining_h4
```

They may be used to form labels or evaluate a hypothesis. They are prohibited from live feature vectors.

The model-regeneration scripts additionally form outcome labels from already-persisted future outcomes. Those labels remain training/evaluation answers only.

## 4. External market-data identity

The large source OHLC files are not duplicated into this Git repository update. Their identity is fixed by filename, coverage and SHA256 in `V10_DATA_AND_LEDGER_MANIFEST_20260916.md`.

Regenerating the feature ledger from a different raw file is not considered the same experiment unless the difference is explicitly documented and revalidated.

## 5. Reference-parity ledger generated after application

The application script joins the existing GitHub bounded-m3 ledger with the new actual-tick signal-execution ledger and creates:

```text
V10_BOUNDED_M3_ACTUAL_TICK_REFERENCE_PARITY_LEDGER_20260916.csv
V10_BOUNDED_M3_ACTUAL_TICK_PARITY_SUMMARY_20260916.csv
V10_BOUNDED_M3_ACTUAL_TICK_PARITY_VALIDATION_20260916.json
```

This is the row-level source for statements such as:

```text
research-selected population
vs
filled population
vs
rejected population
vs
normal-execution subset
vs
exit-contaminated subset
```

The previously published summary remains the expected high-level reference, but the new ledger makes it independently auditable.

## 6. Danger / Persistence model regeneration

The exact lost post-HEAD fitted shock-veto model **is not recovered**.

Instead, this package supplies a deterministic regeneration framework that asks the same research questions while preserving all artifacts required to reproduce the answer.

Generated files:

```text
V10_POST_HEAD_MODEL_REGEN_LEDGER_20260916.csv
V10_POST_HEAD_REGEN_MODEL_COEFFICIENTS_20260916.csv
V10_POST_HEAD_REGEN_SCORE_LEDGER_20260916.csv
V10_POST_HEAD_REGEN_MODEL_METRICS_20260916.csv
V10_K1_DANGER_REGEN_TAIL_SWEEP_20260916.csv
V10_POST_HEAD_REGEN_VALIDATION_20260916.json
```

### Important population boundary

These regenerated heads are:

```text
population = BOUNDED_M3_SELECTED
```

They are **selection-conditioned candidates**. They do not recreate the lost full eligible-universe post-HEAD model and must not be compared as if they were numerically identical to the recorded `+15,013.69` shock-veto experiment.

### Chronological folds

The deterministic regeneration uses:

```text
2025H2 evaluation
<- train only 2025H1

2026 evaluation
<- train only 2025
```

For every fitted head it saves:

- exact feature names;
- training mean and standard deviation;
- coefficient per feature;
- intercept;
- L2 setting;
- training row count and positives;
- per-event test score;
- prior-training percentile rank;
- prior q90 / q95 references;
- evaluation AUC;
- tail-veto economic scan.

No coefficient may live only in terminal output again.

## 7. Current candidate heads in the regeneration script

### K1 danger candidate

Research question:

```text
at the first selected FAST opportunity,
is this an extreme NHA-shock / severe-loss episode?
```

The regenerated target is deliberately explicit:

```text
current FAST bar is the last bar of its run
AND
Child R <= -0.5R
```

This is one reproducible candidate definition, not a claim that it is the only or original definition used in the lost session model.

### K2 persistence candidate

Research question:

```text
at k2,
does at least one more same-color FAST H4 bar exist?
```

Again, this is persistence / confirmation information. It is not assumed to predict the current Child's PnL.

## 8. Post-head descriptive regeneration

The package also regenerates descriptive ledgers from the current exact bounded population, including:

```text
Oracle vs non-Oracle economics
non-Oracle economics by final run length
bounded TP / FP / FN decomposition
universal k1 size-scaling negative control
compact k1/k2 morphology medians
```

These are written as dedicated CSV files. They are intended to prevent descriptive results from surviving only in prose.

## 9. The execution gate still controls the work order

Persisting better ledgers does not cure the first actual-tick implementation defect.

The immediate work order remains:

```text
1. fix immutable EXIT_PENDING persistence
2. rerun exact bounded-m3 entry payload unchanged
3. compare the corrected tick run against the row-level parity ledger
4. verify max concurrent / opposite overlap semantics
5. only then evaluate new Danger / Persistence policy changes on ticks
```

Do not tune the model to compensate for a known execution bug.

## 10. Mandatory research-artifact rule going forward

Any serious new V10 model or state-policy experiment should persist, where applicable:

```text
SOURCE / POPULATION MANIFEST
TRAIN / TEST WINDOW
CAUSAL FEATURE DEFINITION
PREPROCESSING STATE
MODEL COEFFICIENTS OR SERIALIZED MODEL
PER-EVENT SCORE
PRIOR-ONLY THRESHOLD / PERCENTILE REFERENCE
ACTION / SIZE DECISION
OUTCOME / REGRET
RUN-LEVEL / EXPOSURE SUMMARY
VALIDATION RECEIPT
```

If a result cannot be reproduced because one of these was omitted, classify it as session-recorded evidence rather than executable authority.

## 11. Exact resume sequence after this update

After the normal V10 startup order:

```text
1. read V10_POST_HEAD_RESEARCH_CHECKPOINT_20260916.md
2. read V10_BOUNDED_M3_ACTUAL_TICK_VALIDATION_20260916.md
3. read this reproducibility checkpoint
4. read V10_DATA_AND_LEDGER_MANIFEST_20260916.md
5. inspect V10_REGENERATION_RESULTS_20260916.md
6. follow V10_NEXT_RESEARCH_CONTRACT_EXECUTION_FIDELITY_AND_DANGER_REGEN_20260916.md
7. run scripts/v10_validate_repro_pack.py before using regenerated artifacts
```

## 12. Authority status

Nothing in this checkpoint promotes:

- bounded m3;
- the old recorded shock-veto result;
- the new regenerated danger head;
- the new regenerated persistence head;
- any percentile cutoff;
- any fixed exposure map;
- any production EA.

This update improves evidence quality and reproducibility. It does not grant strategy authority.
