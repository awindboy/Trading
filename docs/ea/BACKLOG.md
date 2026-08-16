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
- Old Phase 4B scenario planning and Phase 4C final-source contact/sweep authorization: SUPERSEDED pending corrected reimplementation.
- Phase 5A CHoCH work remains BLOCKED until corrected Phase 4B/4C Root-based ownership passes.

## P1 — Baseline implementation

- [x] Market structure
- [x] Liquidity — Phase 2 physical detector verified
- [ ] Objective selection — old Phase 4B family logic retained for later regression; corrected scenario attachment pending
- [ ] Root OB — Phase 3A core verified; internal-swing completeness audit still open
- [x] Optional LTF child audit — D-124 Root-primary/no-child-gate smoke PASS; audit-only observations do not alter strategy source
- [x] HTF Root contact — D122A physical observation baseline causal PASS
- [ ] Scenario-authorized mature sweep — corrected Root-based ownership/timing pending; child has no gate/ownership authority
- [ ] Structural Reaction liquidity authorization — corrected Root-based ownership/timing re-audit pending
- [ ] M1 CHoCH
- [ ] Entry
- [ ] SL
- [ ] TP
- [ ] Pending cancellation
- [x] H4 long-horizon liquidity index — Phase 2 invariant verified
- [ ] Hierarchical bootstrap / working-set pruning — corrected Root-watch bootstrap pending validation
- [ ] Managed scenario/exposure identity by symbol + magic
- [ ] Minimum-volume parity sizing
- [x] Same-timestamp MTF processing order
- [ ] OnTradeTransaction ticket/history reconciliation

## P2 — Validation

- [x] Compile/run D122A internal build 0.80
- [x] D122A real-tick Root-watch / Root-contact / optional-child temporal causal smoke
- [x] Verify zero historical pre-contact child authorization
- [x] Verify scenario/sweep/order authorization remained disabled during D122A
- [x] Compile/run D-124 internal build 0.81
- [x] Verify every qualifying Root contact becomes Root context READY regardless of child
- [x] Verify optional child observations never create strategy-source children or veto Root context
- [ ] Corrected Phase 4B scenario/objective-family smoke
- [ ] Corrected Phase 4C Root/sweep ownership smoke
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
