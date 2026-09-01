# V8-A-N normalized movement result pack

Status: `RESEARCH-ONLY`

This directory contains the compact result tables underlying:

`docs/ea/v8/V8_A_N_ATR_NORMALIZED_MOVEMENT_RESEARCH_20260901.md`

Key files:

- `allm5_base_rate_stability.csv` — fixed-$10 vs ATR-normalized base rates.
- `excursion_distribution_by_year.csv` — absolute and ATR-normalized future excursion quantiles.
- `normalized_surface_event_metrics.csv` — outer-year AUC/Brier/base-rate by ATR barrier/horizon.
- `normalized_fresh75_movement_results.csv` — fresh-75 realized movement rates for 1.25/1.50/2.00 ATR.
- `fixed_fresh75_cross_target_comparison.csv` — same old fixed-$10 fresh trigger evaluated at fixed and normalized targets.
- `fresh75_exit_surface.csv` — mandatory-direction fixed-dollar and ATR exit development surface.
- `fresh75_exit_robust_summary.csv` — cross-year robustness summaries.
- `surface_monotonicity_audit.csv` — independent-distance probability-order violations.
- `metrics_k*.csv` — compact metrics for each prototype normalized barrier.

Large per-M5 score ledgers are excluded intentionally.

Prototype model coefficient packs are under:

`config/v8_a_n_models_20260901/`

They are research artifacts only and must not be treated as live-authority coefficients.
