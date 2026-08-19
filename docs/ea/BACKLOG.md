# EA Backlog

## Multi-symbol robustness / risk sizing — 2026-08-20

- [x] Design tester-selectable sizing modes: minimum-volume control / fixed account-currency risk / equity-percent risk.
- [x] Implement account-currency Entry->SL risk sizing with `OrderCalcProfit`.
- [x] Normalize risk-sized volume downward to symbol MIN/MAX/STEP without exceeding target risk.
- [x] Preserve minimum-volume parity behavior as the historical sizing control.
- [x] Add diagnostic `OrderCalcMargin` estimate while retaining `OrderCheck` as execution-feasibility authority.
- [x] Extend compact logs with sizing, actual-fill risk, and realized money fields for pooled cross-symbol analysis.
- [ ] MetaEditor compile build 1.92R1L3.
- [ ] Short GOLD minimum-volume parity smoke against 1.92R1L2: trade identities/Entry/SL/TP/order volume must remain unchanged.
- [ ] Fixed-risk smoke on at least two symbols with different volume steps; planned risk must never exceed target.
- [ ] Equity-percent smoke; target risk must equal preflight equity snapshot × configured percent.
- [ ] Run ~10 symbols over one common 1-year window with frozen Expansion V1 and identical risk protocol.
- [ ] Produce per-symbol and pooled robustness report; pooled result is not yet a synchronized portfolio-DD test.
- [ ] Only after cross-symbol evidence, decide whether to build a synchronized multi-symbol portfolio harness.

## Current research checkpoint — 2026-08-20

Completed since the previous repository checkpoint:

- [x] Recover exact 2025 build-1.91 raw ledger and re-run frozen PLAN-time regime formulas.
- [x] Reject weak-progression BAD veto after 2025 sign reversal.
- [x] Reject `directional_advance_norm > 1/3` as the V1 persistence replacement after 2025 failure.
- [x] Freeze Regime Research V1 as `M30_CLEAN_PERSISTENT_EXPANDING` before opening 2022.
- [x] Implement standalone direct MT5 research EA with Parent and Expansion modes.
- [x] Independently verify 2,338 Development continuation regime decisions with zero formula/verdict mismatches.
- [x] Complete 2023–2025 direct Parent run.
- [x] Complete 2023–2025 direct Expansion V1 run.
- [x] Verify every Expansion Development trade is an exact Parent trade and Expansion removes a net-negative 22-trade subset.
- [x] Add `RESEARCH_COMPACT` / `FULL_AUDIT` logging modes for long runs; logging-only semantics.
- [x] Add `V1_REGIME_BASELINE_NO_GATE` research-harness comparator without changing the baseline execution chain.
- [x] Open and complete the first sealed 2022 OOS only after V1 freeze.
- [x] 2022 direct Baseline / Parent / Expansion comparison completed with zero execution divergence.
- [x] 2022 Regime Research V1 satisfies every pre-registered PASS condition.
- [x] 2022 Expansion improves Parent on both expectancy and drawdown.

Immediate next work:

- [ ] Run preferred final untouched 2021 direct confirmation with the frozen V1 unchanged.
- [ ] Compare 2021 Baseline `EXTERNAL_CONTINUATION` / Parent / Expansion under identical direct MT5 conditions.
- [ ] Decide explicitly whether Regime Research V1 should be promoted into current strategy authority.
- [ ] If promoted, update `AGENTS.md`, `EA_SPEC.md`, baseline implementation identity, and regression fixtures in one controlled change.
- [ ] If any regime formula/threshold is changed after 2022, call it V2 and do not reuse 2022 as untouched OOS evidence.
- [ ] Separately implement recoverable pending-cancel retry by exact broker ticket and run execution-parity regression; do not mix this with regime-model changes.

## P0 — Before coding

- [ ] Map AGENTS.md rules to deterministic definitions.
- [ ] Audit `mentor_engine/structure.py`.
- [ ] Audit `mentor_engine/liquidity.py`.
- [ ] Audit `mentor_engine/zones.py`.
- [ ] Audit `mentor_engine/execution.py`.
- [ ] Audit `mentor_engine/planner.py`.
- [ ] Audit `ICTCockpitIndicator.mq5`.
- [ ] Audit `MentorScenarioTraderEA.mq5`.
- [ ] Produce reuse / replace / reject matrix.

## Current implementation checkpoint

- Phase 1.1 structure/bootstrap causal audit: PASS.
- Phase 2 liquidity/sweep physical-detector causal audit: PASS.
- Phase 3A HTF Root OB core causal audit: PASS within implemented scope.
- Root lifecycle balance from the historical Phase 3A run: `272 = 161 PRICE_INVALIDATED + 110 STRUCTURE_INVALIDATED + 1 ACTIVE`.
- Full Root completeness for independent structurally-meaningful internal-swing contexts remains open.
- Old Phase 3B pre-contact child refinement: SUPERSEDED by D-122.
- D122A build 0.80 temporal causal test: PASS.
- D-124 build 0.81 Root-primary / optional-child audit: PASS; 11 Root contacts → 11 ROOT_CONTEXT_READY, optional child observations=2, strategy-source children=0.
- Old Phase 4B/4C child/refined-source authorization: SUPERSEDED.
- D-125 corrected Phase 4B build 0.90: PASS; 13 PLANs / 6 preplanned contacts / 5 no-preplan contacts / retrospective planning 0.
- D-126 build 1.00 Root-reaction sweep implementation: causal smoke PASS; 11 AUTHORIZED_SWEEP / 20 pools. Its extra Root-ownership filters are historical and superseded by D-127.
- D-127 build 1.10 linear trigger pipeline: PASS in both LAST_OPPOSITE baseline and FVG-origin experiment runs; detector/sequence separation verified.
- D-133 FVG-origin OB baseline + same-entry Root contributor merge: ACTIVE.
- D-134 hedging-account same-direction independent add-ons: ACTIVE.
- D-135 performance working-set optimization: PASS.
- D-135A build 1.91 canceled-pending lifecycle hotfix: 2025 full-year parity PASS; one recoverable cancel-reject retry edge remains from the separate 2023–2024 run.
- Regime Research V1 direct harness: Development validation PASS / 2022 first OOS PASS; not yet baseline strategy authority.

## P1 — Baseline implementation

- [x] Market structure
- [x] Liquidity — Phase 2 physical detector verified
- [x] Objective selection — D-125 corrected Root-specific pre-contact family freeze causal smoke PASS
- [ ] Root OB — Phase 3A core verified; internal-swing completeness audit still open
- [x] Optional LTF child audit — D-124 Root-primary/no-child-gate smoke PASS; audit-only observations do not alter strategy source
- [x] HTF Root contact — D122A physical observation baseline causal PASS
- [x] Scenario Sweep stage — D-127 first direction-compatible M1_SWEEP_DETECTED after Root contact; baseline 6/6, experiment-on 33/36
- [ ] Structural Reaction liquidity authorization — corrected Root-based ownership/timing re-audit pending
- [x] M1 CHoCH — D-127 M1_CHOCH_DETECTED mirrors STRUCTURE_PROTECTED_BREAK exactly; 2 baseline / 18 experiment scenario branches accepted
- [x] Entry — D-128B implemented in integrated build 1.50
- [x] SL — D-128B outward 20%-width tick normalization implemented; current primary validation model later set to ROOT_OB_DISTAL_20
- [x] TP — D-128B frozen-family nearest exact >=1R objective selection implemented
- [x] Pending cancellation — D-131 objective/Root/direction authority + broker remove request implemented
- [x] H4 long-horizon liquidity index — Phase 2 invariant verified
- [ ] Hierarchical bootstrap / working-set pruning — D-135 active working-set performance optimization complete; broader historical-bootstrap audit remains open
- [x] Managed scenario/exposure identity by symbol + magic — scenario-scoped hedging execution implemented
- [x] Minimum-volume parity sizing — SYMBOL_VOLUME_MIN implemented
- [x] Same-timestamp MTF processing order
- [x] OnTradeTransaction ticket/history reconciliation — idempotent account/history reconciliation implemented
- [x] Same-entry Root contributor merge — D-133
- [x] Same-direction independent add-on execution — D-134

## P2 — Validation

- [x] Compile/run D122A internal build 0.80
- [x] D122A real-tick Root-watch / Root-contact / optional-child temporal causal smoke
- [x] Verify zero historical pre-contact child authorization
- [x] Verify scenario/sweep/order authorization remained disabled during D122A
- [x] Compile/run D-124 internal build 0.81
- [x] Verify every qualifying Root contact becomes Root context READY regardless of child
- [x] Verify optional child observations never create strategy-source children or veto Root context
- [x] Compile/run D-125 internal build 0.90
- [x] Corrected Phase 4B Root-specific scenario/objective-family smoke
- [x] Verify every bound Root contact has plan_frozen_at < root_contact_at
- [x] Verify same-map multiple Roots are never rejected as AMBIGUOUS_ROOT_LINEAGE
- [x] Verify Root contact without preplan is not retrospectively planned
- [x] Compile/run D-126 internal build 1.00
- [x] D-126 Root/sweep ownership causal smoke
- [x] Verify all D-126 authorized pool available_at < sweep_bar_open
- [x] Verify D-126 same-contact-bar strategic sweep = 0
- [x] Verify all 20 D-126 authorized sweep pools intersected owning Root
- [x] Verify D-126 multiple swept pools remained distinct and no sweep replacement occurred
- [x] Compile/run D-127 internal build 1.10
- [x] Verify M1_SWEEP_DETECTED is detector-only and has no Root/scenario filter
- [x] Verify SCENARIO_SWEEP_ACCEPTED uses only post-contact ordering + direction
- [x] Verify M1_CHOCH_DETECTED mirrors independent M1 STRUCTURE_PROTECTED_BREAK
- [x] Verify SCENARIO_CHOCH_ACCEPTED is strictly later than scenario Sweep and moves to WAITING_FVG
- [x] Verify Root reintersection / sweep-time protected reference / latest-sweep replacement are absent
- [x] FVG_ORIGIN_OB=true causal/additive smoke — baseline scenario rows preserved; 18 branches / 9 distinct accepted CHoCH events
- [x] Implement D-128A causal M1 FVG detector/freshness/widest-selection stage after SCENARIO_CHOCH_ACCEPTED
- [x] D-128A invariants carried into later integrated long-run baseline builds
- [x] Implement D-128B Entry / 20%-width SL / frozen-objective TP geometry in integrated build 1.50
- [x] D-133 same-entry contributor merge removes duplicate provenance without Root quality selection
- [x] D-134 same-direction add-on execution and opposite-direction conflict handling validated in long-run baseline
- [x] D-135/D-135A 2025 full-year execution lifecycle parity with zero divergence
- [x] 2023–2025 Development regime-feature discovery and freeze
- [x] 2023–2025 direct Parent / Expansion research execution
- [x] First locked out-of-sample test — 2022 Regime Research V1 PASS
- [ ] Preferred final untouched confirmation — 2021
- [ ] Explicit Regime V1 promotion/no-promotion decision
- [ ] Recoverable pending-cancel retry execution hotfix + regression
- [ ] Final post-hotfix multi-year execution parity/profitability run if the execution hotfix changes broker lifecycle behavior
- [ ] Live/paper forward validation before any production deployment

Historical validation items retained for traceability:

- [ ] Verify every M1_FVG_DETECTED uses strict 60s Candle1->2->3 continuity across the full integrated ledger.
- [ ] Verify every SCENARIO_FVG_CANDIDATE has FVG.available_at > scenario Sweep close and <= CHoCH close across the full integrated ledger.
- [ ] Verify Candle1-before-Sweep / Candle2-Sweep / Candle3-after-Sweep causal cases are not falsely rejected across a dedicated fixture.
- [ ] Verify PRE_SELECTION_RETEST excludes every post-formation touch through CHoCH selection across a dedicated fixture.
- [ ] Verify selected FVG is unique widest in tick-normalized width; exact max tie is NO_TRADE across a dedicated fixture.
- [ ] Verify no post-CHoCH FVG enters the frozen candidate set across a dedicated fixture.
- [ ] Verify exact planned-R eligibility uses reward_ticks >= risk_ticks with no epsilon relaxation across a dedicated fixture.
- [ ] Verify same-cycle submission guard rejects delayed catch-up signals across a dedicated fixture.
- [ ] Verify partial-fill residual pending is canceled once and locks exposure on divergence across a dedicated fixture.
- [ ] Known manual/Codex case regression.

## Deferred

- [ ] OB-only first-entry variant
- [ ] CHoCH+BOS variant
- [ ] Delivery FVG replacement
- [ ] Delivery FVG add-on variant
- [ ] Parameter optimization
- [ ] Live execution

## Integrated baseline execution history — build 1.50 onward

Historical build 1.50 checkpoint:

- [x] D-128A independent causal fresh widest-FVG selection implemented.
- [x] D-128B selected FVG -> Entry / outward 20% SL / frozen-family nearest R>=1 TP implemented.
- [x] D-129 same-epoch fully-authorized branch arbitration implemented fail-closed; later superseded by D-132/D-133 contributor merge.
- [x] D-130 Strategy Tester-only pending preflight/submission implemented with minimum-volume parity and persistent GTC checks.
- [x] D-131 pending objective/Root/direction cancellation + ticket/history reconciliation implemented.
- [x] FVG_ORIGIN_OB was later promoted to a baseline recognizer by D-133.
- [x] Same-entry Root merge was later formalized by D-133.
- [x] Same-direction independent add-ons were later enabled by D-134.
- [x] Long-run runtime was reduced by D-135 while preserving strategy semantics.
- [x] D-135A restored broker-owned canceled-pending lifecycle parity in the 2025 regression.

Current research execution harness is separate from baseline strategy authority and is documented in `REGIME_RESEARCH_2023_2025.md` and `TEST_RESULTS.md`.
