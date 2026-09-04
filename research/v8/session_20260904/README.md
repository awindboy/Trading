# V8 2026-09-04 exact-tick replay sources

These C++ files preserve the exact research-container semantics used for the sizing/deep-action study.

Important:
- They intentionally reference `/mnt/data/...` paths from the research runtime.
- Treat them as source-of-truth algorithm snapshots, not ready-made Windows/MT5 executables.
- `fresh648_events.csv` is stored under `docs/ea/v8/results/v8_grid_sizing_action_20260904/`.
- See `V8_GRID_SIZING_DEEP_ACTION_RESULT_20260904.md` for population, Bid/Ask, gap-censor and action semantics.
- The first 5m look-ahead run is NOT included; `deep5_actions.cpp` is the corrected version that freezes extrema at 5m.
