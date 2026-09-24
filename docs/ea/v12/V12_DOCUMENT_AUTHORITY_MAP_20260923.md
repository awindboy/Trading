# V12 document authority map

As of `2026-09-24`, read V12 authority in this order:

1. `AGENTS_V12.md` — generation boundary and non-negotiable rules;
2. `HANDOFF_V12.md` — shortest current handoff;
3. `RESEARCH_STATE_V12.md` — established facts, unknowns, and current next work;
4. `V12_ORIGIN_AND_CRT_HYBRID_THESIS_20260923.md` — why V12 exists and how CRT,
   HA, Wave, and ML are assembled;
5. `V12_CRT_NUMERIC_OBSERVATION_CONTRACT_20260923.md` — causal states, numeric
   fields, Parent/Child semantics, stops, targets, and ambiguity policy;
6. `V12_MQL5_ENGINEERING_AND_VALIDATION_CONTRACT_20260923.md` — Python/MQL5
   parity, tester modes, order lifecycle, and evidence gates;
7. `V12_SOURCE_REGISTER_20260923.md` — external provenance and authority levels;
8. `V12_RESEARCH_ROADMAP_20260923.md` — staged work and promotion gates;
9. `V12_PHASE1A_NO_ML_BASELINE_CONTRACT_20260923.md` — frozen first-prototype
   entry, risk, destination, expiry, and comparison contract;
10. `results/README.md` — compact result routing;
11. `results/V12_PHASE0_CAUSAL_EVENT_UNIVERSE_20260923.md` — frozen Phase-0
    source, parity, event-count, ambiguity, and reproducibility receipt;
12. `results/V12_PHASE1A_NO_ML_PROTOTYPE_AND_V10_COMPARISON_20260923.md` —
    reproducible consumed-history scorecard, mechanism audit, and failed V10
    replacement decision;
13. `V12_PHASE1B_H4_M5_JOURNEY_AND_V10_OVERLAY_CONTRACT_20260923.md` — frozen
    H4->M5 shadow journey, causal key-level, V10 Child, and FAST-transition
    observation contract.
14. `results/V12_PHASE1B_H4_M5_JOURNEY_AND_V10_OVERLAY_20260923.md` —
    reproducible transition-risk result, V10 relation audit, rejected veto
    interpretations, and next shadow boundary.
15. `V12_PHASE1C_CRT_PROTECTED_CARRY_AND_REPAIR_CONTRACT_20260924.md` — frozen
    selected-Child Parent-clock carry, unfinished-target, and one-repair-Child
    shadow contract.
16. `results/V12_PHASE1C_CRT_PROTECTED_CARRY_AND_REPAIR_20260924.md` —
    reproducible carry/repair result, concentration audit, rejected broad carry,
    and rolling-target next boundary.
17. `V12_PHASE1D_TEMPORAL_EVENT_STATE_CONTRACT_20260924.md` — frozen broker-
    clock, calendar-cluster, causal surprise, V10 Child, and FAST-flip contract.
18. `results/V12_PHASE1D_TEMPORAL_AND_EVENT_STATE_20260924.md` — reproducible
    temporal/event result, rejected shortcuts, and retained shadow interactions.
19. `V12_PHASE1E_SESSION_WEEKDAY_EVENT_INTERACTION_CONTRACT_20260924.md` —
    corrected calendar clock, DST-aware session/weekday, interaction, and
    uncertainty contract.
20. `results/V12_PHASE1E_SESSION_WEEKDAY_EVENT_INTERACTION_20260924.md` —
    reproducible session/weekday/CRT/event result and retained shadow boundary.
21. `V12_PHASE1F_PARENT_TARGET_SUCCESSION_CONTRACT_20260924.md` — frozen
    monotonic target succession, completed-H4 reframe, same-price cluster, and
    no-family-score contract.
22. `results/V12_PHASE1F_PARENT_TARGET_SUCCESSION_20260924.md` — reproducible
    target-density audit, rejected completeness gate, and retained lifecycle
    coordinate.

## Schema authority

- `../../../research/v12/v12_crt_event_contract.schema.json` defines the current
  machine-readable decision/outcome record boundary.
- `../../../research/v12/validate_v12_event_schema.py` verifies the schema and
  its embedded examples.
- `../../../research/v12/v12_broker_clock_spec.json` freezes broker-label bucket
  and point semantics.
- `../../../research/v12/build_v12_phase0.py` and
  `../../../research/v12/validate_v12_phase0_output.py` are the Phase-0 oracle
  and complete-pack validator.
- `../../../research/v12/v12_phase1a_contract.json`,
  `../../../research/v12/build_v12_phase1a.py`, and
  `../../../research/v12/validate_v12_phase1a_output.py` define and validate the
  first no-ML prototype.
- `../../../research/v12/v12_phase1a_release_manifest.json` is its compact
  retained hash and result receipt.
- `../../../research/v12/v12_phase1b_contract.json` is the machine-readable
  Phase-1B contract.
- `../../../research/v12/build_v12_phase1b.py`,
  `../../../research/v12/validate_v12_phase1b_output.py`, and
  `../../../research/v12/v12_phase1b_release_manifest.json` define, validate,
  and receipt the independently reproduced Phase-1B pack.
- `../../../research/v12/v12_phase1c_contract.json`,
  `../../../research/v12/build_v12_phase1c.py`,
  `../../../research/v12/v12_phase1c_core.py`,
  `../../../research/v12/validate_v12_phase1c_output.py`, and
  `../../../research/v12/v12_phase1c_release_manifest.json` define, validate,
  and receipt the independently reproduced Phase-1C pack.
- `../../../research/v12/v12_phase1d_contract.json`,
  `../../../research/v12/build_v12_phase1d.py`,
  `../../../research/v12/test_v12_phase1d.py`,
  `../../../research/v12/validate_v12_phase1d_output.py`, and
  `../../../research/v12/v12_phase1d_release_manifest.json` define, validate,
  and receipt the independently reproduced Phase-1D pack.
- `../../../research/v12/v12_phase1e_contract.json`,
  `../../../research/v12/v12_calendar_time_overrides.json`,
  `../../../research/v12/build_v12_phase1e.py`,
  `../../../research/v12/test_v12_phase1e.py`,
  `../../../research/v12/validate_v12_phase1e_output.py`, and
  `../../../research/v12/v12_phase1e_release_manifest.json` define, validate,
  and receipt the independently reproduced Phase-1E pack.
- `../../../research/v12/v12_phase1f_contract.json`,
  `../../../research/v12/v12_phase1f_core.py`,
  `../../../research/v12/build_v12_phase1f.py`,
  `../../../research/v12/test_v12_phase1f.py`,
  `../../../research/v12/validate_v12_phase1f_output.py`, and
  `../../../research/v12/v12_phase1f_release_manifest.json` define, validate,
  and receipt the independently reproduced Phase-1F pack.

## Predecessor routing

- V11: `../v11/HANDOFF_V11.md` and
  `../v11/results/V11_NEW_SKELETON_PHASE_AND_PROGRESS_LADDER_DIAGNOSTIC_20260923.md`.
  V11 is frozen; Wave Candle remains an observation asset.
- V10: `../v10/HANDOFF_V10.md` and `../v10/RESEARCH_STATE_V10.md`. V10 is a
  frozen HA/ML comparator and feature/parity component library.

Predecessor documents cannot override V12.

## Result boundary

Phase 1A is the first V12 performance result, but only on consumed development
evidence. It is reproducible and directly compared with V10; it fails the V10
replacement gate. It is not independent validation, MQL5 parity, actual-tick
economics, or trade authority. Phase 1B is complete and reproducible on consumed
evidence. Its stop-risk partition is diagnostic only and grants no action.
Phase 1C is complete and reproducible on consumed evidence. Its broad carry is
rejected and its target-led and repair subsets remain too sparse and
concentrated for action.
Phase 1D is corrected and reproducible on consumed evidence. Phase 1E is
complete and reproducible. Time, session, weekday, and events are retained as
state coordinates, not a session/news veto, sizing map, or directional oracle.
Phase 1F is complete and reproducible. The nearest rolling one-use target is
too dense to distinguish trustworthy unfinished Parents: every Phase-1C bridge
remains unfinished. Target completeness is rejected as a gate; target kind is
retained only as a lifecycle coordinate.
