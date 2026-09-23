# Scripts index

Do not infer active authority from a filename. Read `AGENTS.md` and the active
generation map first.

## Active V12 research

V12 code begins under `research/v12/`, not this directory. Phase 0 currently has
the event schema and validator. The next accepted implementation is a causal
raw-M1 W1->H4 and D1->H1 event-universe builder.

## Workspace and operations

- `check_workspace_structure.py`: repository structure/manifest check;
- `trading_journal_launcher.py`: local journal launcher;
- `install_mt5_ea.py`, `install_mt5_indicator.py`: MT5 installation helpers;
- `check_mt5_journal_pipeline.py`, `watch_mt5_journal_pipeline.py`: journal pipeline checks;
- `check_pine_static.py`: TradingView static check.

## Historical research systems

- `v9_*`: frozen V9 causal/chart-native tools;
- `mentor_*`, Ground Truth builders, and their tests: separate historical
  research lineage;
- other `build_*`, replay, and reverse-engineering scripts: reproduction assets.

Historical scripts do not create V12 candidates or authority unless a V12
contract explicitly imports their role.
