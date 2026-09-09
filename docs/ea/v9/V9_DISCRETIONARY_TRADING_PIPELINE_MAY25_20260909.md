# V9 Discretionary Trading Pipeline — May 2025 Historical Pointer

Date: `2026-09-09`
Status: `CONSUMED / HISTORICAL FIRST-PASS PIPELINE / SUPERSEDED FOR NEW TRADING`
Market: `GOLD# ONLY`

This file was the active May first-pass discretionary trading pipeline at Git HEAD:

`147df4b74ff90135374991152a7b7338becd86ee`

Its historical rules included:

- future-hidden exact-prefix replay;
- real pre-entry Hard SL;
- Parent/Child separation;
- `WHAT IS NEW?` for same-side retries;
- H1 campaign-health review;
- Stochastic/EMA shadow-only instrumentation;
- no automatic BE/partial/trail;
- no hindsight rescue/backfill.

May completion found that these high-level rules were insufficient to guarantee cross-session compliance. The first pass drifted through directional asymmetry, hidden no-chase/minimum-room filters, and confusion between Child independence and pitch quality.

Do not use this file as current trading authority.

Current authority is:

- `AGENTS_V9.md`
- `HANDOFF_V9.md`
- `RESEARCH_STATE_V9.md`
- `DECISIONS_V9_MAY25_HARNESS_ADDENDUM_20260909.md`
- `results/V9_MAY25_COMPLETION_AND_HARNESS_POSTMORTEM_20260909.md`
- `V9_DISCRETIONARY_TRADING_PIPELINE_JUN25_20260909.md`
- `V9_NEXT_RESEARCH_CONTRACT_JUN25_AUDITABLE_DISCRETION_20260909.md`

For exact historical May-pipeline wording, use Git history at the commit above. Do not reconstruct current rules from this consumed file.
