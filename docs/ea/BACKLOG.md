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
- D122A Root-contact → post-contact child implementation: prepared in internal build 0.80; local compile and real-tick causal validation pending.
- Old Phase 4B scenario planning and Phase 4C final-source contact/sweep authorization: SUPERSEDED pending corrected reimplementation.
- Phase 5A CHoCH work remains BLOCKED until D122A and corrected Phase 4B/4C pass.

## P1 — Baseline implementation

- [x] Market structure
- [x] Liquidity — Phase 2 physical detector verified
- [ ] Objective selection — old Phase 4B family logic retained for later regression; corrected scenario attachment pending
- [ ] Root OB — Phase 3A core verified; internal-swing completeness audit still open
- [ ] LTF refinement — D122A post-contact implementation prepared; compile/real-tick validation pending
- [ ] HTF Root contact — D122A physical observation implemented; compile/real-tick validation pending
- [ ] Scenario-authorized mature sweep — intentionally disabled until post-contact child/sweep timing is frozen
- [ ] Structural Reaction liquidity authorization — intentionally disabled pending D-122 ownership/timing re-audit
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

- [ ] Compile D122A internal build 0.80 in MetaEditor
- [ ] D122A real-tick Root-watch / Root-contact / post-contact-child causal smoke
- [ ] Verify zero historical pre-contact child authorization
- [ ] Verify scenario/sweep/order authorization remains disabled during D122A
- [ ] Corrected Phase 4B scenario/objective-family smoke
- [ ] Corrected Phase 4C child/sweep ownership smoke
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
