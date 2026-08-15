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
- Phase 2 liquidity/sweep causal audit: PASS.
- Phase 3A HTF Root OB core causal audit: PASS within implemented scope.
- Root lifecycle balance: `272 = 161 PRICE_INVALIDATED + 110 STRUCTURE_INVALIDATED + 1 ACTIVE`.
- Full Root completeness for independent structurally-meaningful internal-swing contexts remains open.
- Phase 3B targeted M30/M15/M5 causal refinement implemented.
- Phase 3B compile/smoke verification: pending.
- Scenario/source-contact/order authority remains disabled.

## P1 — Baseline implementation

- [x] Market structure
- [x] Liquidity — Phase 2 core verified
- [ ] Objective selection — Phase 4B family freeze implemented; R/final TP pending execution geometry
- [ ] Root OB — Phase 3A core verified; internal-swing completeness audit still open
- [x] LTF refinement — Phase 3B extended child-path validation PASS
- [ ] Source touch
- [x] Sweep — physical detector verified
- [ ] M1 CHoCH
- [ ] Entry
- [ ] SL
- [ ] TP
- [ ] Pending cancellation
- [x] H4 long-horizon liquidity index — Phase 2 invariant verified
- [ ] Hierarchical bootstrap / working-set pruning
- [ ] Managed scenario/exposure identity by symbol + magic
- [ ] Minimum-volume parity sizing
- [x] Same-timestamp MTF processing order
- [ ] OnTradeTransaction ticket/history reconciliation

## P2 — Validation

- [ ] Phase 4B scenario/objective-family smoke
- [x] Phase 4A map/reversal-permission smoke
- [x] Phase 3B extended refinement coverage — CHILD_CREATED=7 / CHILD_INVALIDATED=6
- [x] Phase 3A Root core smoke / causal CSV audit
- [x] Phase 2 liquidity/sweep smoke / CSV causal audit
- [x] Phase 1.1 structure smoke / causal log audit
- [x] Compile Phase 1 with zero errors
- [ ] Recompile Phase 1.1 and resolve behavior-affecting warnings
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