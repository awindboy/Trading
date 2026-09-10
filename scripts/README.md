# Scripts Index

Do not select an active research path from filenames alone.
Read the authority document for the project/version first.

## V9 — active chart-native research path

V9 authority starts at:

`docs/ea/v9/AGENTS_V9.md`

Current V9 research flow:

```text
v9_causal_m1.py
-> v9_ict_object_engine.py
-> v9_chart_native_packet.py
-> AI MAP selection
-> v9_replay_event_runner.py
-> TRIGGER / Child
-> v9_hard_stop_guard.py + mapped review events
```

Active V9 tools:

- `v9_causal_m1.py`
  - fail-closed authoritative M1 verification, reveal, advance, snapshot;
- `v9_ict_object_engine.py`
  - exact H4/H1 FVG, OB-candidate, swing/liquidity candidate geometry and lifecycle;
  - candidate universe only; no strategic importance authority;
- `v9_chart_native_packet.py`
  - two-chart `MAP + TRIGGER` renderer using AI-selected object IDs;
- `v9_replay_event_runner.py`
  - advances a causal replay to the first frozen price/zone/bar-close event;
- `v9_hard_stop_guard.py`
  - independent Hard SL first-touch guard on an already-revealed prefix;
- `v9_causal_numeric_replay.py`
  - historical numeric replay helper; check current V9 authority before use;
- `test_v9_ict_object_engine.py`
  - geometry/lifecycle unit tests for the current candidate engine.

V9 production/EA authority is `NONE`.
Do not use these research tools for live capital deployment.

## Ground Truth V2 / Mentor Replay V5

This is a separate research lineage governed by its own root authority.

- `build_mentor_api_contracts.py`
- `build_ground_truth_v2.py`
- `mentor_replay_v4_core.py`
- `mentor_ai_replay_v4.py`
- `mentor_ai_live_v4.py`
- associated integration/regression tests

Do not mix its strategy authority with V9.

## Web journal / MT5 operations

- `trading_journal_launcher.py`
- `install_mt5_ea.py`, `install_mt5_indicator.py`
- `check_mt5_journal_pipeline.py`, `watch_mt5_journal_pipeline.py`
- `test_ea_event_pipeline.py`
- `generate_ai_trade_feedback.py`, `import_mentor_feedback_to_journal.py`

## TradingView

- `check_pine_static.py`

## Workspace maintenance

- `check_workspace_structure.py`

## Legacy / research reproduction

Other historical `build_*`, `run_mentor_*`, replay, reverse-engineering, and manual-ground-truth scripts may be retained for reproducibility.
Check their governing documents and archived-output paths before use.
