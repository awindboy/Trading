# V13 document authority map

As of `2026-09-29`, this package was extended against GitHub `main`
`1555d2b06b4dabdbadf14366c26e4f2177506463`. Always refresh `main` first.

## Active read order

1. `AGENTS_V13.md`
2. `V13_OBJECTIVE_AND_EVALUATION_UPDATE_20260928.md`
3. `HANDOFF_V13.md`
4. `RESEARCH_STATE_V13.md`
5. `V13_HA_RESEARCH_ROADMAP_20260926.md`
6. `V13_HA_RESEARCH_ROADMAP_STATUS_ADDENDUM_20260928.md`
7. `V13_BASELINE0_HA_MAX10_CONTRACT_20260926.md`
8. historical HA-3..HA-8/X1/X2 contracts and their receipts as needed
9. `V13_FULL_RESEARCH_CHRONICLE_20260929.md`
10. `V13_LTF_BRANCH_DECISION_LOG_20260929.md`
11. `V13_LTF_ROUTE_Q75_Q50_ACTION_CONTRACT_20260929.md`
12. `results/V13_LTF_ROUTE_Q75_Q50_RESEARCH_RECEIPT_20260929.md`
13. `V13_LTF_ROUTE_Q75_Q50_MQL5_VALIDATION_PROTOCOL_20260929.md`
14. `results/V13_LTF_ROUTE_Q75_Q50_ACTUAL_TICK_REPLAY_RECEIPT_20260929.md`
15. HA-9 action/coverage documents and earlier LTF checkpoint receipts as history
16. `../../../mt5/experts/V13HAOnlyMax10EA.mq5` — frozen comparator EA
17. `../../../mt5/experts/V13SA1CleanContinuationEA.mq5` — actual-tick reference EA
18. `../../../mt5/experts/V13LTFRouteQ75Q50_PolicyReplayEA.mq5` — Reconstruction A replay EA

## Precedence

- V13 controls active research; V12 and earlier are historical evidence.
- Baseline-0 contract controls comparator semantics.
- `V13_OBJECTIVE_AND_EVALUATION_UPDATE_20260928.md` controls **current evaluation
  priority** where earlier prose treated right-tail preservation as the dominant
  reason to reject an action.
- Frozen historical experiment contracts/receipts still control what those old
  experiments did and what they measured. They are not rewritten retroactively.
- The LTF route q75/q50 contract controls the current research candidate.
- Its receipt distinguishes session-reported results from locally saved and
  actual-tick-verified evidence.
- Reconstruction A actual-tick MT5 evidence controls its execution economics
  over the M1 idealized proxy. It does not retroactively reproduce the absent
  interrupted-session q50 ledger.
- The supplied actual-tick report controls the reconstructed Child economics in
  the trade-mode receipts, but it does not replace event-reason parity because
  the tester Journal/event stream was not supplied.

## Current strategy/research boundary

Baseline 0 remains frozen. SA-1 remains the ordinary-quality actual-tick
reference. LTF-route Reconstruction A now has a saved, hashed event ledger and
exact actual-tick Journal parity, but is not promoted because its superior net
comes with worse loss frequency, win rate, streak and exposure than SA-1. Its
compiled replay EA is an execution harness, not production or capital-sizing
authority.
