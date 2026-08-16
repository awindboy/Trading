# EA Backlog

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
- [x] Entry — D-128B implemented in integrated build 1.50; final validation pending
- [x] SL — D-128B outward 20%-width tick normalization implemented; final validation pending
- [x] TP — D-128B frozen-family nearest exact >=1R objective selection implemented; final validation pending
- [x] Pending cancellation — D-131 objective/Root/direction authority + broker remove request implemented; final validation pending
- [x] H4 long-horizon liquidity index — Phase 2 invariant verified
- [ ] Hierarchical bootstrap / working-set pruning — D-125 bootstrap Root PLAN freeze smoke covered; broader pruning remains open
- [x] Managed scenario/exposure identity by symbol + magic — integrated execution lock implemented; final validation pending
- [x] Minimum-volume parity sizing — SYMBOL_VOLUME_MIN implemented; final validation pending
- [x] Same-timestamp MTF processing order
- [x] OnTradeTransaction ticket/history reconciliation — idempotent account/history reconciliation implemented; final validation pending

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
- [ ] Final integrated build 1.50 A/B run replaces the skipped isolated D-128A smoke; validate D-128A invariants inside the combined ledger
- [ ] Verify every M1_FVG_DETECTED uses strict 60s Candle1->2->3 continuity
- [ ] Verify every SCENARIO_FVG_CANDIDATE has FVG.available_at > scenario Sweep close and <= CHoCH close
- [ ] Verify Candle1-before-Sweep / Candle2-Sweep / Candle3-after-Sweep causal cases are not falsely rejected
- [ ] Verify PRE_SELECTION_RETEST excludes every post-formation touch through CHoCH selection
- [ ] Verify selected FVG is unique widest in tick-normalized width; exact max tie is NO_TRADE
- [ ] Verify no post-CHoCH FVG enters the frozen candidate set
- [ ] Verify exact planned-R eligibility uses reward_ticks >= risk_ticks with no epsilon relaxation
- [ ] Verify same-cycle submission guard rejects delayed catch-up signals
- [ ] Verify partial-fill residual pending is canceled once and locks exposure on divergence
- [x] Implement D-128B Entry / 20%-width SL / frozen-objective TP geometry in integrated build 1.50
- [x] Resolve concurrent fully-authorized Root branches fail-closed as AMBIGUOUS_SIMULTANEOUS_AUTHORIZATION; no arbitrary score/nearest selection
- [x] Phase 4A map/reversal-permission smoke — independent scope remains valid
- [x] Historical Phase 3B run preserved as old-implementation evidence only — CHILD_CREATED=7 / CHILD_INVALIDATED=6
- [x] Phase 3A Root core smoke / causal CSV audit
- [x] Phase 2 liquidity/sweep physical detector smoke / CSV causal audit
- [x] Phase 1.1 structure smoke / causal log audit
- [x] Compile Phase 1 with zero errors
- [ ] Visual Strategy Tester inspection
- [ ] Known manual/Codex case regression
- [ ] In-sample implementation validation
- [ ] Locked out-of-sample test

## Deferred

- [ ] OB-only first-entry variant
- [ ] CHoCH+BOS variant
- [ ] Delivery FVG replacement
- [ ] Add-on positions
- [ ] Optimization
- [ ] Live execution


## Integrated baseline execution — build 1.50

- [x] D-128A independent causal fresh widest-FVG selection implemented.
- [x] D-128B selected FVG -> Entry / outward 20% SL / frozen-family nearest R>=1 TP implemented.
- [x] D-129 same-epoch fully-authorized branch arbitration implemented fail-closed; no arbitrary Root selector.
- [x] D-130 Strategy Tester-only pending preflight/submission implemented with minimum-volume parity and persistent GTC checks.
- [x] D-131 pending objective/Root/direction cancellation + ticket/history reconciliation implemented.
- [ ] MetaEditor compile build 1.50.
- [ ] January real-tick integrated run with `InpEnableFvgOriginObExperiment=false`.
- [ ] Identical integrated run with `InpEnableFvgOriginObExperiment=true`.
- [ ] Audit FVG -> geometry -> objective -> arbitration -> preflight -> orders -> fills -> exits/cancels.
- [ ] Decide whether FVG_ORIGIN_OB remains experiment or is promoted only after completed-trade evidence.
- [ ] Revisit same-direction provenance merge only if fail-closed arbitration materially discards otherwise identical completed signals; do not invent a selector.
