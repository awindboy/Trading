# V12 research code inventory

V12 is the active CRT/HA/Wave/ML hybrid research generation.

## Retained Phase-0 artifacts

- `v12_crt_event_contract.schema.json`: machine-readable boundary between a
  causal decision record and a later outcome record. It contains synthetic
  examples only.
- `validate_v12_event_schema.py`: dependency-free integrity check for the schema,
  examples, OHLC invariants, hash/timestamp format, and C2-branch direction map.
- `v12_broker_clock_spec.json`: frozen MT5 broker-label bucket, point-grid,
  completion, cutoff, and holdout policy.
- `v12_phase0_core.py`: dependency-free causal aggregation, ATR, C2
  classification, stable-ID, and event-record primitives.
- `build_v12_phase0.py`: exhaustive raw-M1 Phase-0 builder and MT5 timeframe
  parity audit.
- `test_v12_phase0.py`: synthetic boundary, classification, ambiguity, ID, and
  holdout-reader tests.
- `validate_v12_phase0_output.py`: complete pack, hash, parent-ID, schema, and
  summary validator.
- `v12_phase0_release_manifest.json`: compact retained receipt for the two
  byte-identical Phase-0 builds.

Run:

```powershell
python research/v12/validate_v12_event_schema.py
python research/v12/test_v12_phase0.py
python research/v12/build_v12_phase0.py
python research/v12/validate_v12_phase0_output.py
```

Passing these validations establishes a reproducible parent-event universe. It
does not prove CRT, HA, Wave, ML, or trading performance.

## Retained Phase-1A artifacts

- `v12_phase1a_contract.json`: machine-readable rejection-only entry, risk,
  destination, expiry, ambiguity, and comparison contract.
- `v12_phase1a_core.py`: pure trigger selection, next-parent lookup, M1 guards,
  outcome, scorecard, and counterfactual primitives.
- `build_v12_phase1a.py`: complete no-ML builder from the Phase-0 pack and raw
  M1 through the frozen cutoff.
- `test_v12_phase1a.py`: synthetic trigger, weekend C3, guard, gap, ambiguity,
  and terminal-outcome regression tests.
- `validate_v12_phase1a_output.py`: full output-hash, decision/outcome,
  scorecard, counterfactual, and V10-invariant validator.
- `render_v12_phase1a_summary.py`: deterministic summary render generated from
  the scorecard and comparison CSVs.
- `v12_phase1a_release_manifest.json`: compact retained receipt for two
  independently rebuilt, byte-identical output packs.

Run:

```powershell
python research/v12/test_v12_phase1a.py
python research/v12/build_v12_phase1a.py
python research/v12/validate_v12_phase1a_output.py
```

The Phase-1A result is a consumed-history mechanism diagnostic. It fails the
V10 replacement gate and has no trade authority.

## Next retained implementation

Keep Phase 1A frozen. Phase 1B has predeclared the next observation pipeline:

- `v12_phase1b_contract.json`: H4->M5 shadow CRT activations, completed-period
  key-level lifecycle, canonical journey state, V10 Child context, and FAST-flip
  explanation contract. It has no result or action authority yet.

The implementation must keep CRT decisions, journey outcomes, V10 decision
context, V10 outcomes, FAST-flip context, and later run outcomes physically
separate. HA/Wave sensor ablation and ML remain later and shadow-only.

Large ledgers and diagnostics belong under ignored `output/`.

## Predecessor reuse boundary

V10/V11 code may provide tested OHLC aggregation, HA, ATR normalization, Wave,
feature-registry, and parity utilities. Reuse requires explicit imports or copied
functions with a named role and tests. V10 selected-event ledgers may be used only
as comparators; they cannot seed V12 candidates.
