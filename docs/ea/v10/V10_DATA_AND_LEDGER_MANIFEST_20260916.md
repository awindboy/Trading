# V10 Data and Ledger Manifest

Date: `2026-09-16`  
Status: `ACTIVE RESEARCH DATA-LINEAGE MANIFEST / NOT STRATEGY AUTHORITY`  
Package base GitHub main HEAD: `f5bd80136b152a2508213c6d8ef77642062a4ebe`

## 1. Purpose

This manifest identifies the exact data and ledger chain required to reproduce the current V10 bounded-m3 actual-tick audit and the new post-head selected-signal feature/model-regeneration artifacts.

A matching filename without a matching SHA256 is not assumed to be the same source.

## 2. External market-data sources

These large source files are intentionally **not duplicated** in the Git update. They are referenced by exact identity and were used to build the persisted selected-signal feature ledger.

| Timeframe | Source filename | Rows | Coverage | SHA256 |
|---|---|---:|---|---|
| M15 | `GOLD#_M15_202201030100_202608282345.csv` | 110,018 | 2022-01-03 01:00 → 2026-08-28 23:45 | `245902105a2c36a627768f979584984944aabc9e62dfa3cfc9acb3198544c269` |
| M30 | `GOLD#_M30_202201030100_202608282330.csv` | 55,012 | 2022-01-03 01:00 → 2026-08-28 23:30 | `8a3124d0f67ec6f8729b495011899cd4ca4fb5fd723dce7998f09614a12a1022` |
| H1 | `GOLD#_H1_202201030100_202608282300.csv` | 27,522 | 2022-01-03 01:00 → 2026-08-28 23:00 | `c1d9f63f8af4d7dddd9e20e6eb124dc71de51015384b9c61a772d5981c7be52c` |
| H4 | `GOLD#_H4_202201030000_202608282000.csv` | 7,199 | 2022-01-03 00:00 → 2026-08-28 20:00 | `5e12fa91f974c0f15e340ea8116bd9168fc6821e6309592cee1a7e197675de09` |

The M1 source remains the broader causal execution/research source in the project, but this reproducibility pack's new MTF feature ledger is regenerated from the four files above plus the selected event timestamps.

## 3. Raw Strategy Tester evidence committed in this update

Stored under:

```text
docs/ea/v10/results/raw/
```

| File | Bytes | SHA256 |
|---|---:|---|
| `V10_BOUNDED_M3_ACTUAL_TICK_EVENTS_RAW_20260916.csv` | 303,603 | `eea7f54a4f0a70aa3c3ea52b38163f95fe8f79de93cdf0ccf8d73cc8fcc91f69` |
| `V10_BOUNDED_M3_ACTUAL_TICK_REPORT_RAW_20260916.xlsx` | 451,365 | `83b3b5311b229ef9adb2754ac4475d174d3fb6d1337332b0a39738d6216be83c` |

The raw tester workbook is preserved as evidence. The reproducibility scripts parse it using Python standard-library ZIP/XML readers; they do not rewrite the workbook.

## 4. Precomputed row-level actual-tick ledgers

These are generated directly from the two raw Strategy Tester files and are included in the update so later research does not depend on reparsing the workbook first.

| Ledger | Rows | Role |
|---|---:|---|
| `V10_BOUNDED_M3_ACTUAL_TICK_SIGNAL_EXECUTION_LEDGER_20260916.csv` | 1,159 | canonical selected-signal → execution mapping |
| `V10_BOUNDED_M3_ACTUAL_TICK_ENTRY_REJECT_LEDGER_20260916.csv` | 175 | 174 market-closed + 1 SL-already-touched selected entries |
| `V10_BOUNDED_M3_ACTUAL_TICK_EXIT_REJECT_EVENT_LEDGER_20260916.csv` | 134 | individual rejected FAST-NHA close requests |
| `V10_BOUNDED_M3_ACTUAL_TICK_EXIT_REJECT_INCIDENT_LEDGER_20260916.csv` | 84 | reject incidents grouped by timestamp |
| `V10_BOUNDED_M3_ACTUAL_TICK_EXIT_REJECT_AFFECTED_LEDGER_20260916.csv` | 131 | filled positions whose holding was materially contaminated |
| `V10_BOUNDED_M3_ACTUAL_TICK_PENDING_EXIT_DELAY_LEDGER_20260916.csv` | 131 | intended versus actual exit delay per affected Child |
| `V10_BOUNDED_M3_ACTUAL_TICK_DEALS_LEDGER_20260916.csv` | 1,968 | normalized MT5 deals |
| `V10_BOUNDED_M3_ACTUAL_TICK_ORDERS_LEDGER_20260916.csv` | 1,968 | normalized MT5 orders |
| `V10_BOUNDED_M3_ACTUAL_TICK_EXPOSURE_PATH_LEDGER_20260916.csv` | 1,968 | exposure state after each deal |
| `V10_BOUNDED_M3_ACTUAL_TICK_OVERLAP_EPISODE_LEDGER_20260916.csv` | 33 | simultaneous long/short exposure episodes |
| `V10_BOUNDED_M3_ACTUAL_TICK_SL_EXECUTION_LEDGER_20260916.csv` | 252 | structural SL intended-risk vs actual execution |
| `V10_BOUNDED_M3_ACTUAL_TICK_PERIOD_DIRECTION_SUMMARY_20260916.csv` | 9 | compact time/direction rollup |

Validation receipts:

- `V10_BOUNDED_M3_ACTUAL_TICK_LEDGER_VALIDATION_20260916.json`
- `V10_BOUNDED_M3_ACTUAL_TICK_EXTENDED_VALIDATION_20260916.json`

Expected fixed facts include:

```text
selected signals                 1,159
fills                              984
market-closed entry rejects        174
SL-already-touched rejects           1
exit reject requests                134
exit reject incidents                84
exit-reject affected positions      131
structural SL positions             252
max gross exposure                   16 units
opposite overlap                311.0125 hours
```

## 5. Persisted causal selected-signal feature ledger

`V10_POST_HEAD_SELECTED_SIGNAL_FEATURE_LEDGER_20260916.csv`

```text
rows = 1,159
columns = 62
direction mismatches = 0
```

Validation receipt:

`V10_POST_HEAD_SELECTED_SIGNAL_FEATURE_LEDGER_20260916.validation.json`

The receipt also stores the SHA256 of every raw market-data source used.

### Answer-sheet-only columns

```text
answer_final_run_len
answer_future_remaining_h4
```

These must never be added to a live feature vector.

## 6. Existing GitHub source ledgers used after application

This package intentionally does not duplicate the large ledgers already present on current V10 main. The application/regeneration scripts read them from the target repository.

Primary dependency:

```text
docs/ea/v10/results/V10_BOUNDED_M3_ENTRY_LEDGER_2025_2026.csv
```

Expected selected population inside it:

```text
W > 0
-> 1,159 rows
-> 2,313 units
```

The broader existing V10 evidence set remains indexed by `docs/ea/v10/results/README.md`.

## 7. Artifacts generated by the application script

### 7.1 M1-reference ↔ actual-tick parity

```text
V10_BOUNDED_M3_ACTUAL_TICK_REFERENCE_PARITY_LEDGER_20260916.csv
V10_BOUNDED_M3_ACTUAL_TICK_PARITY_SUMMARY_20260916.csv
V10_BOUNDED_M3_ACTUAL_TICK_PARITY_VALIDATION_20260916.json
```

### 7.2 Selection-conditioned post-head model regeneration

```text
V10_POST_HEAD_MODEL_REGEN_LEDGER_20260916.csv
V10_POST_HEAD_REGEN_MODEL_COEFFICIENTS_20260916.csv
V10_POST_HEAD_REGEN_SCORE_LEDGER_20260916.csv
V10_POST_HEAD_REGEN_MODEL_METRICS_20260916.csv
V10_K1_DANGER_REGEN_TAIL_SWEEP_20260916.csv
V10_POST_HEAD_REGEN_VALIDATION_20260916.json
```

### 7.3 Descriptive regeneration

```text
V10_POST_HEAD_ORACLE_NONORACLE_ECONOMICS_REGEN_20260916.csv
V10_POST_HEAD_NONORACLE_RUN_LENGTH_ECONOMICS_REGEN_20260916.csv
V10_POST_HEAD_BOUNDED_FP_FN_DECOMPOSITION_REGEN_20260916.csv
V10_POST_HEAD_BOUNDED_K1_SCALE_SCAN_REGEN_20260916.csv
V10_POST_HEAD_MORPHOLOGY_MEDIANS_REGEN_20260916.csv
```

### 7.4 Narrative and artifact integrity

```text
docs/ea/v10/V10_REGENERATION_RESULTS_20260916.md
results/V10_REPRODUCIBILITY_ARTIFACT_SHA256_20260916.csv
```

## 8. Script lineage

```text
RAW ACTUAL-TICK EVENTS + TESTER XLSX
    |
    +-> v10_build_actual_tick_ledgers.py
    |      -> signal execution / rejects / deals / orders
    |
    +-> v10_build_actual_tick_extended_ledgers.py
           -> exit incidents / pending delays / exposure / overlap / SL execution

M15 + M30 + H1 + H4 + selected event timestamps
    |
    +-> v10_build_post_head_feature_ledger.py
           -> selected-signal causal MTF feature ledger

existing GitHub bounded-m3 ledger
+ signal execution ledger
    |
    +-> v10_join_reference_execution.py
           -> row-level research-vs-tick parity

existing GitHub bounded-m3 ledger
+ selected MTF feature ledger
+ signal execution ledger
    |
    +-> v10_join_and_regen_models.py
    |      -> merged regeneration ledger
    |      -> preprocessing / coefficients / scores / metrics / danger tail sweep
    |
    +-> v10_regen_post_head_descriptives.py
           -> economic and morphology descriptive ledgers

all generated outputs
    |
    +-> v10_write_regen_summary.py
    +-> v10_write_artifact_manifest.py
    +-> v10_validate_repro_pack.py
```

## 9. Research data governance

- All periods represented by these artifacts are consumed research evidence.
- Future run length and eventual trade outcome are permitted only as answer-sheet labels.
- A stopped Child remains dead.
- Actual-tick chronology is higher authority for execution questions.
- The first actual-tick run remains execution-contaminated until `EXIT_PENDING` persistence is fixed and rerun.
- The newly regenerated model is selection-conditioned and is not claimed to be the lost post-head full-universe model.
- No percentile or fitted coefficient in the regeneration becomes production authority by being persisted.

## 10. Artifact hash manifest

After application, run:

```text
python scripts/v10_write_artifact_manifest.py .
```

This creates:

`docs/ea/v10/results/V10_REPRODUCIBILITY_ARTIFACT_SHA256_20260916.csv`

It is the compact integrity index for the reproducibility artifacts.

<!-- V10_DECISION_CLOCK_HOTFIX_MANIFEST_20260916_START -->
## Decision-clock lineage correction

Canonical fields after the 2026-09-16 hotfix:

```text
baseline decision_ts
<-> EA effective_ts
<-> execution ledger decision_time
<-> feature ledger decision_time
```

Execution chronology is preserved separately as:

```text
entry_event_time
entry_time_actual
```

The first actual-tick evidence contains 34 filled rows whose event/fill tick occurred after the effective signal clock: 33 by one second and one by two seconds. These are not signal mismatches.
<!-- V10_DECISION_CLOCK_HOTFIX_MANIFEST_20260916_END -->
