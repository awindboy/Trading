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
9. `results/README.md` — compact result routing;
10. `results/V12_PHASE0_CAUSAL_EVENT_UNIVERSE_20260923.md` — frozen Phase-0
    source, parity, event-count, ambiguity, and reproducibility receipt.

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

## Predecessor routing

- V11: `../v11/HANDOFF_V11.md` and
  `../v11/results/V11_NEW_SKELETON_PHASE_AND_PROGRESS_LADDER_DIAGNOSTIC_20260923.md`.
  V11 is frozen; Wave Candle remains an observation asset.
- V10: `../v10/HANDOFF_V10.md` and `../v10/RESEARCH_STATE_V10.md`. V10 is a
  frozen HA/ML comparator and feature/parity component library.

Predecessor documents cannot override V12.

## Result boundary

There is no V12 performance result yet. The Phase-0 receipt establishes input and
parent-event reproducibility only. A schema, architecture, candidate count, or
passing parity check is not profitability or independent validation evidence.
