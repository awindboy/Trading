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

## Retained Phase-1B artifacts

- `v12_phase1b_contract.json`: frozen H4->M5 shadow journey, key-level, V10
  overlay, simultaneous-conflict, and immutable-origin-target contract.
- `v12_phase1b_core.py`: one-use liquidity, FAST/STD/SLOW HA, canonical journey,
  conflict, failure, milestone-stage, and stable-ID primitives.
- `build_v12_phase1b.py`: raw-M1 causal builder for CRT decisions, journeys,
  unchanged V10 Children, FAST flips, scorecards, diagnostics, and render.
- `test_v12_phase1b.py`: equality/breach, gap birth-consumption, journey ordering,
  replacement, conflict, failure, cutoff, and HA regression tests.
- `validate_v12_phase1b_output.py`: complete-pack hash, ID, cutoff,
  decision/outcome, and frozen-V10 invariant validator.
- `render_v12_phase1b_summary.py`: deterministic Pillow evidence card.
- `v12_phase1b_release_manifest.json`: compact retained receipt for two
  independently rebuilt, byte-identical packs.

Run:

```powershell
python -m unittest discover -s research/v12 -p "test_v12_phase*.py"
python research/v12/build_v12_phase1b.py <frozen arguments>
python research/v12/validate_v12_phase1b_output.py <output> --expected-prefix-sha256 04e074...
```

Phase 1B is a consumed-history transition diagnostic. It identifies a stable
stop-risk partition at FAST flips but grants no veto, delay, sizing, EA, or
trade authority. HA/Wave conditional ablation and ML remain shadow-only.

## Retained Phase-1C artifacts

- `v12_phase1c_contract.json`: frozen Parent-clock carry, unfinished-origin-
  target, and one-repair-Child semantics.
- `v12_phase1c_core.py`: pure eligibility, target-state, guard, exposure, stop-
  chain, drawdown, and scorecard helpers.
- `build_v12_phase1c.py`: Phase-1B/V10 overlay reader plus chronological raw-M1
  Hard-SL and Parent-terminal guard replay.
- `test_v12_phase1c.py`: target timing, same-Parent eligibility, repair identity,
  long/short guard, and concurrency regression tests.
- `validate_v12_phase1c_output.py`: complete-pack, decision/outcome, prefix,
  count, and frozen-V10 invariant validator.
- `v12_phase1c_release_manifest.json`: compact receipt for two independently
  rebuilt, byte-identical output packs.

Run:

```powershell
python -m unittest discover -s research/v12 -p "test_v12_phase1c.py"
python research/v12/build_v12_phase1c.py <frozen arguments>
python research/v12/validate_v12_phase1c_output.py <output> --expected-prefix-sha256 04e074...
```

Phase 1C rejects broad active-Parent carry. Its unfinished-origin-target and
repair subsets are sparse and concentrated, so neither has action authority.
The next structural object is a causal rolling Parent target inventory.

## Retained Phase-1D artifacts

- `v12_phase1d_contract.json`: frozen broker-clock, calendar-cluster, causal
  surprise, market-window, V10 Child, and FAST-flip observation contract.
- `build_v12_phase1d.py`: strict raw-M1 prefix reader, MT5 calendar quality
  audit, matched-week event response, frozen-ledger join, scorecards, and Pillow
  summary renderer.
- `test_v12_phase1d.py`: causal event-proximity boundary and exposure/right-tail
  metric regression tests.
- `validate_v12_phase1d_output.py`: manifest, hash, cutoff, calendar-conflict,
  clock-alignment, and frozen-ledger validator.
- `v12_phase1d_release_manifest.json`: compact receipt for two independently
  rebuilt, byte-identical packs.

Run from `research/v12`:

```powershell
python -m unittest test_v12_phase1d.py
python build_v12_phase1d.py --calendar <MT5 common snapshot> --output <output>
python validate_v12_phase1d_output.py <output>
```

Phase 1D proves that broker clock and scheduled/realized event state are useful
coordinates. It rejects fixed-hour, all-news, and surprise-direction shortcuts.
Its retained interactions have no veto, sizing, EA, or trade authority.

## Retained Phase-1E artifacts

- `v12_phase1e_contract.json`: fixed UTC+3 broker-clock, DST-aware session,
  weekday, interaction, and uncertainty contract.
- `v12_calendar_time_overrides.json`: exact-ID, official-source correction for
  the one anomalous 2025-11-20 Employment Situation timestamp.
- `build_v12_phase1e.py`: session/weekday activity, V10 capital, FAST/NHA, H4-
  slot parity, event-family, and week-block bootstrap builder.
- `test_v12_phase1e.py`: session mapping, weekday-boundary, and event-state
  regression tests.
- `validate_v12_phase1e_output.py`: complete-pack, hash, source-clock, cutoff,
  frozen-ledger, and authority validator.
- `v12_phase1e_release_manifest.json`: compact receipt for two byte-identical
  output packs.

Phase 1E establishes that session/weekday state changes immediate whipsaw risk,
but high-stop phases often carry the largest right tail. It does not authorize
a session, weekday, event, or joint-state veto or sizing rule.

Large ledgers and diagnostics belong under ignored `output/`.

## Predecessor reuse boundary

V10/V11 code may provide tested OHLC aggregation, HA, ATR normalization, Wave,
feature-registry, and parity utilities. Reuse requires explicit imports or copied
functions with a named role and tests. V10 selected-event ledgers may be used only
as comparators; they cannot seed V12 candidates.
