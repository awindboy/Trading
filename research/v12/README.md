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

## Retained Phase-1F artifacts

- `v12_phase1f_contract.json`: monotonic origin-to-external target succession,
  completed-H4 reframe, same-price clustering, and no-family-score contract.
- `v12_phase1f_core.py`: pure directional frontier, active-level cluster,
  same-M1 query, target-ID, and Parent-state primitives.
- `build_v12_phase1f.py`: byte-frozen Phase-1B/1C/1E pack join, target ledger,
  V10/FAST/carry/repair contexts, and balanced stop/right-tail scorecards.
- `test_v12_phase1f.py`: family-neutral clustering, same-M1, frontier, pending,
  and Parent-end regression tests.
- `validate_v12_phase1f_output.py`: complete-pack, decision/outcome, frozen-
  population, authority, and manifest validator.
- `v12_phase1f_release_manifest.json`: compact receipt for two independently
  rebuilt, byte-identical packs.

Phase 1F rejects nearest one-use target completeness as a useful gate. Previous-
H4 objects make the inventory nearly always unfinished, including all Phase-1C
bridges and the full H20 pre-event cell. Origin/external target kind remains an
observation-only lifecycle coordinate for conditional HA/Wave work.

## Retained Phase-1G artifacts

- `v12_phase1g_contract.json`: frozen continuous clock, source-box path, event-
  sequence, normalization, fold, and success contract.
- `v12_phase1g_core.py`: DST-aware clock conversion, causal source-box and path
  primitives, train-only encoder, and deterministic ridge estimators.
- `build_v12_phase1g.py`: raw-M1 path reconstruction, V10/FAST/bridge/repair
  joins, walk-forward competing-outcome models, mechanism ablations, and
  capital diagnostics.
- `test_v12_phase1g.py`: DST, strict-break, same-M1 exclusion, reentry, prior-
  daily normalization, train-only vocabulary, and determinism tests.
- `validate_v12_phase1g_output.py`: complete-pack, causal timestamp, frozen-
  population, model-set, authority, and hash validator.
- `v12_phase1g_release_manifest.json`: compact receipt for two independently
  rebuilt, byte-identical 14-file packs.

Run:

```powershell
python research/v12/test_v12_phase1g.py
python research/v12/build_v12_phase1g.py --replace
python research/v12/validate_v12_phase1g_output.py output/v12_phase1g_continuous_intraday_path_20260924_a
```

Phase 1G retains continuous settlement/repair and boundary-consumption paths as
a promising stop-risk representation. It fails the joint right-tail success
gate, cannot forecast FAST run length, and grants no veto or sizing authority.

## Retained Phase-1H artifacts

- `v12_phase1h_contract.json`: frozen 50-field compact competing-risk, train-
  only conviction-band, capital-preservation, stability, and HA/Wave ablation
  contract.
- `v12_phase1h_core.py`: compact path derivatives, raw-M1 H4 HA reconstruction,
  train-only quintile, and capital-allocation primitives.
- `build_v12_phase1h.py`: Phase-1G/Wave/raw-M1 source verification, expanding-
  window dual-head models, train-only bands, shadow tilt, and frozen gates.
- `test_v12_phase1h.py`: threshold, path derivative, capital, completed-H4 HA,
  and 50-field schema regression tests.
- `validate_v12_phase1h.py`: complete-pack, manifest, cutoff, population,
  prediction-grain, train-band, and byte-parity validator.
- `v12_phase1h_release_manifest.json`: compact receipt for two independently
  rebuilt, byte-identical nine-file packs.

Run:

```powershell
python -m unittest test_v12_phase1h.py
python build_v12_phase1h.py --replace
python validate_v12_phase1h.py ../../output/v12_phase1h_compact_conviction_head_20260924_a
```

Phase 1H confirms that compact continuous path can separate stopped exposure,
but the frozen primary capital gate fails. HA adds incremental stop information
without improving the right-tail head; Wave does not add robust incremental
information. This supports separately assembled competing heads, not a veto or
sizing map.

## Retained Phase-1I artifacts

- `v12_phase1i_contract.json`: frozen funded-FAST-run outcome classes, repeat-
  stop target, asymmetric head, train-only threshold, and equal-risk gates.
- `v12_phase1i_core.py`: run classification, causal prior-run state, policy,
  retention, equal-stop-budget, and threshold-selection primitives.
- `build_v12_phase1i.py`: raw-M1/Phase-1G/Phase-1H/Wave verified builder for run
  episodes, walk-forward heads, policy comparators, mechanism contrasts, and
  oracle bounds.
- `test_v12_phase1i.py`: outcome priority, prior-state chronology, unresolved-
  run rejection, capital tradeoff, and train-threshold tests.
- `validate_v12_phase1i.py`: complete-pack, source, cutoff, run-grain, threshold,
  authority, and independent byte-parity validator.
- `v12_phase1i_release_manifest.json`: compact receipt for two independently
  rebuilt, byte-identical ten-file packs.

Phase 1I proves that the repeat-stop objective has valuable oracle headroom but
rejects the available first-decision Path+HA score. The next research object is
the causal within-run divergence timeline, not a broader cooldown or another
static indicator.

## Retained Phase-1J artifacts

- `v12_phase1j_contract.json`: frozen run population, first-stop/weighted-5R
  terminal, completed-M15 event, equal-horizon, and promotion screen.
- `v12_phase1j_core.py`: weighted-tail touch, causal run timeline, path-state,
  event snapshot, effect-size, and AUC primitives.
- `build_v12_phase1j.py`: source-verified raw-M1 timeline, terminal, event,
  occurrence, contrast, and promotion-screen builder.
- `test_v12_phase1j.py`: tail-price, AUC, effect-direction, and event snapshot
  tests.
- `validate_v12_phase1j.py`: complete-pack, causal terminal, manifest, cutoff,
  and independent byte-parity validator.
- `v12_phase1j_release_manifest.json`: compact receipt for two independently
  rebuilt, byte-identical eight-file packs.

Phase 1J finds stable early post-entry damage/progression separation but grants
no action. Its next bounded use is a no-threshold staged-funding counterfactual,
not another entry-time classifier.

## Retained Phase-1K artifacts

- `v12_phase1k_contract.json`: frozen no-threshold progression-release,
  damage-stop, first-Child-only, and capital gate contract.
- `v12_phase1k_core.py`: causal admission and normalized capital primitives.
- `build_v12_phase1k.py`: all-run M15 event reconstruction and unchanged-Child
  counterfactual scorecard builder.
- `test_v12_phase1k.py`, `validate_v12_phase1k.py`, and
  `v12_phase1k_release_manifest.json`: policy-boundary tests, complete-pack
  parity validator, and compact two-build receipt.

Phase 1K rejects using early M15 events as stale permission for existing later
H4 Children. Further work, if retained, must define a genuinely event-native
independent Child rather than another V10 admission gate.

## Retained Phase-1L artifacts

- `v12_phase1l_contract.json`: frozen H4/H1 HA clock, equal-total-stop-budget,
  H4-context, M15-path, continuous-clock, and viability contract.
- `v12_phase1l_core.py`: causal bar aggregation, FAST/STD/SLOW HA, scorecard,
  AUC, concurrency, and equal-stop-budget primitives.
- `build_v12_phase1l.py`: chronological raw-M1 H4/H1/M15 reconstruction,
  historical H4 parity audit, policy scorecards, and feature screens.
- `test_v12_phase1l.py`, `validate_v12_phase1l.py`, and
  `v12_phase1l_release_manifest.json`: regression tests, complete-pack parity,
  and compact two-build receipt.

Phase 1L rejects whole-base H1 HA substitution. H1/M15 path remains a subordinate
observation layer only.

## Retained Phase-1M artifacts

- `v12_phase1m_contract.json`: frozen H1 `k=1` transition-Child, H4 context,
  total-stop-budget, stability, and right-tail contract.
- `build_v12_phase1m.py`: source-verified structural-transition comparator and
  year/side/exposure scorecard builder.
- `validate_v12_phase1m.py` and `v12_phase1m_release_manifest.json`: complete-
  pack byte-parity validator and compact two-build receipt.

Phase 1M retains `k=1` as a coherent event concept but rejects it as entry or
sizing authority. Its lower total stop count is lower frequency, not better
per-attempt quality, and its pooled result is 2023 LONG-tail concentrated.

## Retained Phase-1N artifacts

- `v12_phase1n_contract.json` and `v12_phase1n_core.py`: frozen H1/M15 temporal-
  information populations, causal features, labels, folds, and capital gates.
- `build_v12_phase1n.py` and `analyze_v12_phase1n.py`: source-verified builder
  and broad temporal-band audit.
- `test_v12_phase1n.py`, `validate_v12_phase1n.py`, and
  `v12_phase1n_release_manifest.json`: regression tests, complete-pack parity,
  and compact receipt.

Phase 1N proves lower-clock temporal information is measurable but rejects its
broad use as an admission filter because right-tail capital collapses.

## Retained Phase-1O artifacts

- `v12_phase1o_contract.json` and `v12_phase1o_core.py`: frozen after-one-stop
  sequence features, train-only policy, and stability/capital primitives.
- `build_v12_phase1o.py`: H1/M15 sequence-interaction and policy builder.
- `test_v12_phase1o.py`, `validate_v12_phase1o.py`, and
  `v12_phase1o_release_manifest.json`: tests, complete-pack parity, and receipt.

Phase 1O retains H1 after-stop nonlinear state as a hypothesis but rejects
promotion because one frozen fold is negative and broad M15 use loses tail.

## Retained Phase-1P artifacts

- `v12_phase1p_contract.json`: frozen H2/M30 clock, feature, policy, and gate
  contract.
- `build_v12_phase1p.py` and `analyze_v12_phase1p.py`: intermediate-clock
  builder and cross-model/capital audit.
- `validate_v12_phase1p.py` and `v12_phase1p_release_manifest.json`: complete-
  pack byte-parity validator and compact receipt.

Phase 1P identifies M30 session/micro path as the leading consumed-data clock
and H2 continuous clock as supportive. All remain research-only.

## Retained Phase-1Q artifacts

- `v12_phase1q_contract.json`: frozen third-and-later-stop cohort and promotion
  gates across H2/H1/M30/M15.
- `build_v12_phase1q.py`: source-verified deep-chain interaction and policy
  builder.
- `validate_v12_phase1q.py` and `v12_phase1q_release_manifest.json`: complete-
  pack byte-parity validator and compact receipt.

Phase 1Q retains M15 session/static state only as a deep-churn observation after
two prior stops. It reduces but does not eliminate stop chains and grants no
veto, delay, sizing, or trade authority.

Large ledgers and diagnostics belong under ignored `output/`.

## Predecessor reuse boundary

V10/V11 code may provide tested OHLC aggregation, HA, ATR normalization, Wave,
feature-registry, and parity utilities. Reuse requires explicit imports or copied
functions with a named role and tests. V10 selected-event ledgers may be used only
as comparators; they cannot seed V12 candidates.
