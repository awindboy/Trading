# V13 document authority map

As of `2026-09-28`, this package was prepared against GitHub `main`
`29e0073e57553d8fe1fd14b843daf09164a7a248`. Always refresh `main` first.

## Active read order

1. `AGENTS_V13.md`
2. `V13_OBJECTIVE_AND_EVALUATION_UPDATE_20260928.md`
3. `HANDOFF_V13.md`
4. `RESEARCH_STATE_V13.md`
5. `V13_HA_RESEARCH_ROADMAP_20260926.md`
6. `V13_HA_RESEARCH_ROADMAP_STATUS_ADDENDUM_20260928.md`
7. `V13_BASELINE0_HA_MAX10_CONTRACT_20260926.md`
8. historical HA-3..HA-8/X1/X2 contracts and their receipts as needed
9. `V13_HA9_ADDON_PROOF_LOCK_ACTION_CONTRACT_20260928.md`
10. `results/V13_HA9_ADDON_PROOF_LOCK_RECEIPT_20260928.md`
11. `V13_HA9_MQL5_VALIDATION_PROTOCOL_20260928.md`
12. `../../../mt5/experts/V13HAOnlyMax10EA.mq5` — frozen comparator EA
13. `../../../mt5/experts/V13HAProofLockMax10EA.mq5` — HA-9 research EA

## Precedence

- V13 controls active research; V12 and earlier are historical evidence.
- Baseline-0 contract controls comparator semantics.
- `V13_OBJECTIVE_AND_EVALUATION_UPDATE_20260928.md` controls **current evaluation
  priority** where earlier prose treated right-tail preservation as the dominant
  reason to reject an action.
- Frozen historical experiment contracts/receipts still control what those old
  experiments did and what they measured. They are not rewritten retroactively.
- HA-9 contract controls the current action candidate only.
- HA-9 receipt controls the exact idealized research numbers reported for that
  candidate.
- Actual-tick MT5 evidence, once produced, controls execution economics over the
  M1 idealized receipt.

## Current strategy/research boundary

Baseline 0 remains frozen. HA-9 is a breakthrough candidate but is not production
or capital-sizing authority. No further indicator/model stack should be added
before HA-9 actual-tick event parity is established.
