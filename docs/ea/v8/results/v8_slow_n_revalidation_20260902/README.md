# V8 Slow-N Downstream Revalidation Tables — 2026-09-02

Status: `DEVELOPMENT / NO PRODUCTION AUTHORITY`

Files:

- `slow_n_phase_comparison.csv`
  - corrected Phase-0 and Phase-2 probability metrics.
- `slow_n_failure_summary.csv`
  - compact negative-control direction results.
- `slow_n_bb_abcd_transfer.csv`
  - predefined BB-A/B/C/D transfer results.
- `slow_n_bb_b_window_phase_robustness.csv`
  - BB-B n=3/5/8, Phase-0/Phase-2, annual robustness.
- `slow_n_tick_overlap_stoch_m1_summary.csv`
  - limited old/new tick-overlap re-synchronization diagnostics.
- `slow_n_mql_parity_reference.csv`
  - deterministic Python reference points for the Phase-0 MT5 indicator.

Raw tick evidence in this directory is **overlap-only**. It must not be confused with a full new-Slow-N tick extraction.

No 2021 data are used.
