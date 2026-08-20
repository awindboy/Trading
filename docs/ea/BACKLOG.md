# EA Backlog

Last updated: 2026-08-20
Current phase: **BASE EDGE AUDIT**
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
- [ ] Specify exact `EDGE_AUDIT_V1` shadow-logging schema.
- [ ] Implement `EDGE_AUDIT_V1` with **zero strategy authority**.
- [ ] Regression: audit harness must produce identical baseline trade identities, Entry, SL, TP, order lifecycle, and R to the non-audit control.
- [ ] Record stage checkpoints: PLAN / ROOT_CONTACT / SWEEP / CHOCH / FVG / ENTRY.
- [ ] Add research-only 15m / 1h / 4h / 24h signed forward-return labels after each horizon elapses.
- [ ] Add research-only MFE / MAE labels by stage.
- [ ] Add same-entry standardized virtual 1R / 2R / 3R barriers.
- [ ] Add direction-flipped mirror virtual 1R / 2R / 3R barriers.
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
