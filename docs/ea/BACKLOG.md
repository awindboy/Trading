# EA Backlog

Last updated: 2026-08-20
Current phase: **D-145 RUNNER MARKET-CONTEXT AUDIT**
Strategy authority: unchanged

## P0 — Base-edge audit

- [x] Complete 2025 18-symbol `BASELINE_NO_REGIME_GATE` run under fixed $100 risk sizing.
- [x] Parse all 18 event ledgers and reconstruct all 1,463 closed trades.
- [x] Separate execution-contaminated symbol-years from divergence-free evidence.
- [x] Re-score divergence-free continuation with strategy-planned barriers to isolate strategy signal from execution-price effects.
- [x] Run first trade-specific stylized barrier-null diagnostic.
- [x] Split base-edge evidence by LONG/SHORT and H1 state.
- [x] Confirm the major 2025 negative result is dominated by bearish continuation rather than broker slippage alone.
- [x] Perform targeted source audit for obvious LONG/SHORT sign inversion in structure/FVG/Entry/SL/objective/order branches; none found.
- [x] Identify D-127 `SEQUENCE_ONLY` causal ownership as a research concern, not yet a proven defect.
- [x] Freeze D-142A `EDGE_AUDIT_V1` stage-forward measurement contract in `docs/ea/EDGE_AUDIT_V1.md`.
- [x] Prepare D-142A build `1.92R1L4` with **zero strategy authority**.
- [ ] MetaEditor compile D-142A `1.92R1L4` with 0 errors.
- [ ] Regression: audit OFF / ON must produce identical baseline trade identities, Entry, SL, TP, order lifecycle, and R.
- [x] Instrument hourly MAP / PLAN / ROOT_CONTACT / SWEEP / CHOCH / FVG / ACTUAL_FILL identity checkpoints.
- [x] Implement D-142A research-only 15m / 1h / 4h / 24h forward-return labels for MAP through FVG.
- [x] Implement D-142A MFE / MAE labels for MAP through FVG.
- [ ] D-142B after D-142A parity: add exact actual-fill same-direction 1R / 2R / 3R tick-order barriers.
- [ ] D-142B after D-142A parity: add direction-flipped mirror 1R / 2R / 3R tick-order barriers.
- [ ] Compare LONG and SHORT stage-by-stage.
- [ ] Determine whether edge is absent at Map, lost at trigger stages, or destroyed by SL/TP geometry.
- [ ] Only after the failure location is known, define one controlled strategy variant.

## P0 — Execution integrity, parallel but separate

### Recoverable cancel-rejection retry

- [x] Confirm original 2023–2024 stale-pending issue.
- [x] Confirm three independent 2025 cross-symbol reproductions with `retcode=10018 / Market closed`.
- [ ] Implement exact-ticket retry for recoverable pending cancel rejection.
- [ ] Keep strategy cancellation required while broker pending remains live.
- [ ] Keep exposure/divergence lock until cancel or fill is proven.
- [ ] Regression-test stale-fill fixtures.

### Pending disappeared without fill/cancel proof

Observed 2025 fixtures:

```text
EURCAD order 42
GBPJPY order 144
GBPUSD order 130
GBPJPY order 224
GBPUSD order 213
```

- [ ] Reconcile exact current-order state against order history, deal history, and position state before declaring divergence.
- [ ] Determine true broker/tester lifecycle cause.
- [ ] Add deterministic reconciliation rule only after cause is proven.
- [ ] Re-run all contaminated 2025 symbol-years after the fix.

### Right-censored year end

- [ ] Restrict new PLAN/entry cohort to 2025 but extend tester horizon into early 2026 until all 2025-origin execution is terminal.
- [ ] Require zero unresolved 2025-origin execution before final 2025 profitability evidence.

## P1 — Simple benchmark controls

After `EDGE_AUDIT_V1` is validated:

- [ ] Freeze a deterministic time-matched/random null protocol.
- [ ] Freeze a simple EMA trend-follow benchmark.
- [ ] Freeze a simple RSI mean-reversion benchmark.
- [ ] Freeze a simple MACD crossover benchmark.
- [ ] Run the same 2025 symbol universe under comparable risk and standardized exits.
- [ ] Compare expectancy, hit rate, MFE/MAE, direction behavior, symbol breadth, and tail dependence.
- [ ] Do **not** tune benchmark parameters aggressively; benchmarks are controls, not new strategy candidates.

## Regime Research V1 — preserved but deprioritized

Completed:

- [x] 2023–2025 regime discovery and V1 freeze.
- [x] Direct Parent implementation.
- [x] Direct Frozen Expansion V1 implementation.
- [x] Formula parity QA across 2,338 Development continuation decisions.
- [x] Direct Development Parent / Expansion comparison.
- [x] 2022 first sealed OOS.
- [x] 2022 V1 PASS under pre-registered contract.
- [x] Preserve exact `M30_CLEAN_PERSISTENT_EXPANDING` formula.

Paused:

- [ ] 2021 direct final confirmation — **HOLD / DO NOT OPEN YET**.
- [ ] Regime V1 promotion/no-promotion decision — **HOLD**.
- [ ] Cross-symbol direct Frozen V1 run — lower priority until base-edge location is understood.

Rules:

```text
Do not tune leg_expansion_ratio.
Do not add thresholds after seeing 2022/2025.
Do not label UNKNOWN as BAD.
Do not mix base-edge redesign into Frozen Regime V1.
```

If Frozen V1 is changed after 2022, the changed model is V2 and 2022 is not untouched OOS for that model.

## Multi-symbol risk sizing — 1.92R1L3

Completed through the 18-symbol run:

- [x] Tester-selectable minimum-volume / fixed-money / equity-percent sizing modes implemented.
- [x] `OrderCalcProfit` Entry->SL account-currency risk calculation implemented.
- [x] Volume normalized downward to symbol MIN/MAX/STEP.
- [x] `OrderCheck` retained as final execution-feasibility authority.
- [x] Compact logging includes target/planned/actual fill risk and realized money.
- [x] 18-symbol fixed-$100 NO-GATE production-scale research run completed.
- [x] Cross-symbol fixed-risk output parsed successfully.

Still useful later:

- [ ] Dedicated minimum-volume parity fixture for 1.92R1L3 if not already retained locally.
- [ ] Dedicated equity-percent smoke if that mode will be used.
- [ ] Synchronized multi-symbol portfolio harness only after a strategy with base edge survives.

## Current implementation checkpoint

Preserved:

```text
D-124 Root-primary / optional-child audit
D-125 Root-specific pre-contact PLAN
D-127 linear trigger pipeline
D-128 FVG / Entry / SL / TP
D-133 same-entry contributor merge
D-134 same-direction hedging add-ons
D-135 performance working sets
D-135A canceled-pending lifecycle hotfix
build 1.91 historical control
1.92R1L3 research harness
```

Current research warning:

```text
D-127 implementation parity = previously validated
D-127 strategy value = NOW UNDER BASE-EDGE AUDIT
```

Implementation correctness and predictive profitability are separate questions.


## P0 — D-143 front-end causal audit — ANALYZED

- [x] D-142A GOLD January audit OFF/ON parity PASS.
- [x] First six-symbol 2025 stage-forward panel analyzed.
- [x] Identify H1 persistent-map direction / owner persistence as front-end priority suspect.
- [x] Apply/compile D-143 `1.92R1L5` and collect the six-symbol 2025 unified panel.
- [ ] Verify unified-ledger audit OFF/ON parity after filtering `EDGE_AUDIT_*`.
- [ ] Re-run BTCUSD / CADJPY / GBPCAD / GOLD / SILVER / USDJPY 2025 with one unified CSV each.
- [ ] Measure INITIAL_BOS and continuation-BOS forward direction accuracy by TF/direction/month.
- [ ] Measure owner age and last-BOS age versus forward direction accuracy and realized trade win rate.
- [ ] Measure compatible Root ordinal within owner versus Root contact response and eventual trade outcome.
- [ ] Compare all created Roots → physical contacts → PLAN-selected Roots → preplanned contacts to locate selection bias.
- [ ] Determine whether Root contact predicts only local reaction or sustained continuation to structural objective.
- [x] Interpret D-143 before resuming exact barrier work; no strategy filter promoted from D-143.

Research target: eventual strategy win rate `>= 50%`; loss filtering alone is not sufficient evidence.

## Historical implementation items still open

- [ ] Root OB internal-swing completeness audit.
- [ ] Structural Reaction liquidity authorization re-audit.
- [ ] Broader historical bootstrap / pruning audit.
- [ ] Dedicated FVG continuity / pre-selection retest / exact widest-tie fixtures.
- [ ] Partial-fill residual pending fixture.
- [ ] Known manual/Codex case regression.

These are not the immediate profitability-research priority unless `EDGE_AUDIT_V1` points to them.

## Deferred strategy variants

- [ ] OB-only first-entry variant
- [ ] CHoCH+BOS variant
- [ ] Delivery FVG replacement
- [ ] Delivery FVG add-on
- [ ] parameter optimization
- [ ] live execution

## Research governance — do not do now

- [ ] Do **not** add `SHORT = OFF`.
- [ ] Do **not** add `planned_R < 16`.
- [ ] Do **not** restore PD as a veto.
- [ ] Do **not** add generic quality score.
- [ ] Do **not** stack D-126 historical filters back into D-127.
- [ ] Do **not** consume 2021.
- [ ] Do **not** promote Frozen Regime V1.
- [ ] Do **not** use contaminated symbol-years as final profitability evidence.

## Decision gates after EDGE_AUDIT_V1

### Gate A — Map has no edge

```text
Map forward outcomes ≈ or < matched null
```

Action:

- re-evaluate the fundamental market-direction model before trigger tuning.

### Gate B — Map/Root have edge, later trigger loses it

Action:

- research one trigger-timing/causal-ownership difference at a time.

### Gate C — Entry has edge under standardized exits, structural TP/SL loses it

Action:

- separate objective/SL geometry research from signal research.

### Gate D — Only a stable pre-registered regime subset has edge

Action:

- resume regime research using direct execution and untouched confirmation.

### Gate E — Mentor chain fails while simple benchmarks survive

Action:

- treat that as evidence against the current Mentor implementation/theory, not as a reason to add more complexity.


## P0 — D-144 reaction / entry exact-tick barrier audit

- [x] Freeze standardized stage-comparison R as the first causal Root-contact market entry to `ROOT_OB_DISTAL_20` distance.
- [x] Freeze target set before the run: `1.0R / 1.5R / 2.0R`, each versus `-1R`.
- [x] Compare SAME_DIRECTION and FLIPPED_DIRECTION at ROOT_CONTACT / SWEEP / CHOCH / FVG.
- [x] Measure ACTUAL_FILL separately with actual `fill_price -> normalized_sl` R.
- [x] Require exact tick first-hit ordering; never infer fill barrier order from M1 OHLC.
- [x] Keep all D-144 output in the same unified `InpEventCsvFile`.
- [ ] MetaEditor compile D-144 `1.92R1L6` with 0 errors.
- [ ] GOLD 2025-01 audit OFF/ON unified-ledger parity smoke.
- [ ] Confirm non-audit rows are identical after filtering `EDGE_AUDIT_*`.
- [ ] Confirm barrier activation/result integrity and zero unexplained duplicates.
- [ ] Run the same six-symbol 2025 panel.
- [ ] Compute stage × direction × target-R win rates and unresolved rates.
- [ ] Test whether Root/Sweep can clear 50% at 1R and whether CHoCH/FVG/Fill destroy that edge.
- [ ] Test whether flipped-direction controls outperform the scenario direction at any stage.
- [ ] Only after this measurement define one strategy variant.

Research guardrails:

```text
No SHORT veto.
No owner-age threshold.
No Root-count cutoff.
No arbitrary ATR/percent R scale.
No CHoCH filter in D-144.
No TP redesign in D-144.
2021 remains untouched.
```

## P0 — D-145 runner market-context audit

- [x] D-144 GOLD exact-tick single-symbol validation completed.
- [x] Confirm GOLD continuation actual Fill reaches +1R before -1R in 30/51 trades (58.82%).
- [x] Confirm +1.5R is 25/51 and +2R is 20/51; do not optimize a fixed TP from these points.
- [x] Identify D-144 runtime cost as multi-stage per-tick tracker fan-out; retire that harness from broad runs.
- [x] Prepare lightweight D-145 build `1.92R1L7`.
- [ ] MetaEditor compile D-145 with 0 errors.
- [ ] GOLD audit OFF/ON non-audit parity smoke.
- [ ] Confirm D-145 tester speed is materially closer to D-143/control than D-144.
- [ ] Collect ACTUAL_FILL background snapshots and FIRST +1R snapshots.
- [ ] Compare +1R winners that fail before 2R vs trades that reach 2R+.
- [ ] Test **relationship direction**, not optimized thresholds, for:
  - current H1/M30 move maturity / remaining structural room;
  - current M30 net directional advance and leg expansion;
  - selected-FVG pre-fill displacement before retest;
  - Fill -> +1R speed and adverse excursion;
  - H1/M30/M1 structural reinforcement or contradiction after Fill.
- [ ] Require consistency across LONG/SHORT and multiple calendar blocks before treating a feature as causal.
- [ ] If GOLD mechanism is coherent, broaden to selected additional symbols; do not brute-force all symbols until the logging/runtime contract is proven.

Research prohibition:

```text
Do not select 1.2R / 1.3R / 1.4R because pooled win rate crosses 50%.
Do not derive age, time, range-position, progression, or displacement cutoffs from this GOLD sample.
Do not use outcome-known data at Fill snapshot.
Do not consume 2021.
```
