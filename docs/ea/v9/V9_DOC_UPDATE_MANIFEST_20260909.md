# V9 April Completion / May Pipeline Update Manifest

Date: `2026-09-09`
Expected base HEAD: `087299c9351233fe9a9d8a8b72c4840a65b93a91`
Scope: `V9 authority consolidation + April evidence + May trading pipeline + causal instrumentation`

## Replaced authority files

- `docs/ea/v9/AGENTS_V9.md`
- `docs/ea/v9/HANDOFF_V9.md`
- `docs/ea/v9/RESEARCH_STATE_V9.md`

## Superseded old NEXT contracts

The following are replaced by short historical stubs so a future session cannot mistake them for current authority:

- `V9_NEXT_RESEARCH_CONTRACT_SCALE_ALIGNED_JOURNEY_20260908.md`
- `V9_NEXT_RESEARCH_CONTRACT_EXIT_DISTANCE_OPEN_ROUTE_20260907.md`
- `V9_NEXT_RESEARCH_CONTRACT_PARENT_JOURNEY_OPPORTUNITY_20260907.md`

Their original text remains in Git history.

## New current documents

- `DECISIONS_V9_APR25_PIPELINE_ADDENDUM_20260909.md`
- `V9_DISCRETIONARY_TRADING_PIPELINE_MAY25_20260909.md`
- `V9_NEXT_RESEARCH_CONTRACT_MAY25_HARD_SL_CAMPAIGN_HEALTH_20260909.md`
- `V9_PAPER_TRADING_JOURNAL_APR25_20260909.md`
- `results/V9_MAR25_REPLAY_CORRECTION_AND_SUMMARY_20260909.md`
- `results/V9_APR25_COMPLETION_AND_PIPELINE_POSTMORTEM_20260909.md`

## New instrumentation

- `scripts/v9_causal_m1.py` — exact revealed-prefix causal helper already used in V9 replay workbench.
- `scripts/v9_hard_stop_guard.py` — scans only an already-revealed M1 prefix and returns the earliest precommitted Hard-SL touch.
- unit tests for both helpers.

No production EA authority is created by this update.

## Audit clarification

- `WHAT IS NEW?` is a reasoning/audit prompt, not a cooldown or maturity veto.
- Stochastic cross-location is prospective shadow research; no band is assumed superior before May evidence.
- P038's May protective stop is a grandfathered one-time risk cap, not an initial-SL template.
