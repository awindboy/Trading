# V12 document authority map

As of `2026-09-23`, read V12 authority in this order:

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
  Phase-1B contract. No result exists until its complete pack is independently
  reproduced and routed here.

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
economics, or trade authority. Phase 1B is contract-frozen and implementation-
active; it has no result yet.
