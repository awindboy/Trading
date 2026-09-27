# V13 results

Status: `HA-0..HA-6 OBSERVATION COMPLETE / HA-7 REJECTED / HA-8A FIRST MODEL DIAGNOSTIC COMPLETE-NO ACTION / EXACT-WINDOW OFFICIAL ECONOMIC RECEIPT STILL PENDING`

Store compact source-backed receipts here. Generated feature/label CSVs and large
raw/tester artifacts remain outside Git unless explicitly promoted.

## Baseline / execution receipts

- `V13_EXECUTION_13002_TEST_RECEIPT_20260926.md` — execution-recovery tests;
  not economic evidence.
- `V13_BASELINE0_EXTENDED_ACTUAL_TICK_DIAGNOSTIC_20260926.md` — extended real-
  tick structural-parity diagnostic; not official exact-window economics.

## HA-0 through HA-5

- `V13_HA0_MEASUREMENT_RECEIPT_20260927.md`
- `V13_HA1_MORPHOLOGY_PERSISTENCE_RECEIPT_20260927.md`
- `V13_HA2_LIFECYCLE_GIVEBACK_RECEIPT_20260927.md`
- `V13_HA3_REPRESENTATION_COMPARISON_RECEIPT_20260927.md`
- `V13_HA4_D1_STANDARD_HA_RECEIPT_20260927.md`
- `V13_HA4_H1_STANDARD_HA_RECEIPT_20260927.md`
- `V13_HA4C_D_INTEGRATED_STATE_RECEIPT_20260927.md`
- `V13_HA5_CAUSAL_RAW_SWING_RECEIPT_20260927.md`

These receipts establish the causal standard-HA ledger, morphology/lifecycle,
alternate representations, D1/H1 context and raw-swing complement. None grants
a trade rule.

## HA-6 complementary-family receipts

- `V13_HA6A_HASTOC_OBSERVATION_RECEIPT_20260927.md` — published HASTOC formula
  parity; strong pooled ordering but substantial morphology/H1 redundancy and
  long-tail false warnings. Candidate model feature only.
- `V13_HA6B_MOVING_AVERAGE_CONTEXT_RECEIPT_20260927.md` — separate EMA50 regime
  and EMA20 envelope observations. Slower context, no alignment/exit authority.
- `V13_HA6C_ATR_NORMALIZATION_RECEIPT_20260927.md` — ATR14 reduces cross-era
  price-unit drift; ATR is normalization only, not signal/risk authority.
- `V13_HA6D1_ADX_WILDER_RECEIPT_20260927.md` — ADX/DMI audit. ADX weak/unstable,
  DMI largely MA-redundant, tail false warnings; HA-6D branch stop. SuperTrend
  not tested.
- `V13_HA6E_TICK_VOLUME_PARTICIPATION_RECEIPT_20260927.md` — broker tick-volume
  semantics/data quality, same-slot normalization, persistent-H1 participation
  interaction; no universal volume filter/exit authority.

## HA-7 first action receipt

- `V13_HA7_FIRST_ACTION_CHILD_ADMISSION_RECEIPT_20260927.md` — frozen single
  Child-admission experiment. **Rejected**: 89 Children skipped, net -77.93
  points versus Baseline, realized-Journey DD +30.91 worse, and +341.09 points
  removed from 15 long-Journey Children. No EA change and no threshold tuning.

## HA-8A first state-model diagnostic

- `V13_HA8A_COMBINATION_MODEL_RECEIPT_20260928.md` — frozen chronological
  logistic-model ladder across H4/H1, HASTOC, normalized tick activity,
  causal raw swing and EMA50. Modest three-H4 flip prediction increment, but
  highest-risk add-on Children remained net-positive because of long-Journey
  continuation winners. **Observation only; no model/action promotion.**

## Cross-stage synthesis

Read `../V13_HA6_HA7_RESEARCH_SYNTHESIS_20260927.md` for the cross-stage
mechanism interpretation and the reason HA-8A is now justified. Exact stage
numbers/caveats still come from the individual receipts above.

## Reproducible source for HA-6/HA-7

The documentation package adds these scripts under `research/v13/`:

```text
ha6a_hastoc_audit.py
ha6b1_ema50_context_audit.py
ha6b2_ema20_envelope_audit.py
ha6c_atr_normalization_audit.py
ha6d1_adx_wilder_audit.py
ha6e_tick_volume_audit.py
ha6e2_h1_opposition_participation_audit.py
ha7_child_admission_audit.py
```

Compact JSON summaries are included in the documentation ZIP under
`evidence/v13/ha6_ha7/` for audit convenience, but they are not intended to
become Git authority unless explicitly promoted. Large decision CSVs are omitted.

## Official Baseline-0 receipt still required

Expected authority file:

`V13_BASELINE0_MT5_ACTUAL_TICK_RESULT_20260926.md`

Required setup remains:

```text
GOLD#
H4
Every tick based on real ticks
2024-01-01 .. 2026-08-28
10,000 USD
1:100 leverage unless authority is explicitly revised
hedging mode
current execution revision
```

Record EA revision/hash, tester build/broker, report filename/hash and all metrics
required by `../V13_MQL5_BACKTEST_PROTOCOL_20260926.md`.
