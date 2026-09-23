# V10 compact result packs

Repository results are compact receipts, manifests, and decision summaries only. Large per-event ledgers, search grids, bootstrap draws, raw tester exports, and temporary model artifacts belong under ignored `output/` or in Git history.

## `r3_k1stop_20260917/`

Purpose: reproduce and audit the narrow K1 extreme-STOP shadow candidate.

Key files:

- `V10_R3_REPRODUCIBILITY_RECEIPT_20260917.json`
- `V10_R3_K1STOP_FUTURE_SHADOW_MANIFEST_20260917.json`
- `V10_R3_K1STOP_POLICY_FRONTIER_20260917.csv`
- `V10_R3_K1STOP_STABLE_FRONTIER_VALIDATION_20260917.json`
- `V10_R3_R2_UNIVERSE_PARITY_20260917.json`

The remaining files in this pack are the fixed head metrics, tuned/stable frontier metrics, bootstrap summaries, feature/model ablations, and validation receipts named by the reproducibility receipt. None is a live ledger.

Status: consumed historical research and future-shadow instrumentation only.

`V10_R3_R2_UNIVERSE_PARITY_20260917.json` preserves the original path of its R2 comparator so the immutable receipt remains hash-valid. That large comparator ledger was removed from the current tree and is recoverable from Git history at `438f6b4`.

## `r7_sizing_20260917/`

Purpose: compact R6/R7G sizing and M1 economic receipts.

Retained files describe overall/year economics, spread sensitivity, concurrency, feedback summary, and the M1-verified R7G audit. Row-level feedback actions, R6 search receipts, and exploratory subgroup scans were removed.

- `M1_DETAILED_OVERALL.csv` / `M1_DETAILED_YEAR.csv` — overall and annual R4/R7G economics;
- `M1_POLICY_BY_YEAR_R_AND_PNL.csv` — annual structural-R and raw-price PnL;
- `M1_CONCURRENT_RISK_UNITS.csv` — maximum simultaneous units;
- `M1_SPREAD_ADJUSTED_RISK_SUMMARY.csv` / `M1_SPREAD_STRESS_SUMMARY.csv` — cost sensitivity;
- `M1_UPGRADE_OVERALL.csv` — incremental upgraded-Child result;
- `R7G_FEEDBACK_METRICS.csv` / `R7G_FEEDBACK_SUMMARY.csv` — feedback-overlay diagnostics;
- `V10_R7_M1_VERIFIED_ECONOMIC_AUDIT_20260917.md` — interpretation and limitations.

Status: frozen historical comparator, not sizing authority.

## `r7g_ea_20260920/`

Purpose: feature registry, model-export receipt, and R4/R5/R7G parity manifests for the two retained research EAs.

- `FEATURE_REGISTRY.json` — final 84-coordinate registry;
- `IMPLEMENTATION_MANIFEST.json` — implementation identity and hashes;
- `MODEL_EXPORT_PARITY_RECEIPT.json` — exported-model caveat;
- `R4_ACTION_PARITY.json` — R4 action parity;
- `R5_EV_PARITY_VS_R7L.json` — R5 EV sign parity;
- `R7G_RUNTIME_PARITY_RECEIPT.csv` — feedback/final sizing parity;
- `V10_R3_CAUSAL_M1_UNIVERSE_MANIFEST.json` — raw-M1 universe identity.

Status: executable research evidence only. User MT5 execution exists, but market-closed order failures and final production lifecycle handling remain unresolved/deferred.

## Local outputs

Current scripts regenerate local evidence under ignored `output/`. Those files are intentionally not committed because they are large, derivable, and not authority.

## `ma_band_forward_20260921/`

Purpose: compact receipt for the first causal post-cutoff normalized MA-band observation window through `2026-09-18 23:57`.

- `V10_MA_BAND_FORWARD_ANALYSIS_AUDIT.json` — source identities, sample counts, and no-action boundary;
- `V10_MA_BAND_FORWARD_FEATURE_AUDIT.csv` — fixed-coordinate STOP AUC and FAST-run bootstrap intervals;
- `V10_MA_BAND_FORWARD_CONCENTRATION.csv` — direction/stage concentration.

The row ledger and extended raw M1 remain under ignored `output/`. This pack does not contain or authorize a threshold, composite score, or trade action.
