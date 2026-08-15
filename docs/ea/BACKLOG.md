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

- Phase 1.1 structure/bootstrap smoke + causal log audit: PASS.
- Phase 2 liquidity/sweep CSV audit: PASS.
- Phase 2 H4 external-only invariant: PASS.
- Phase 2 same-bar / single-consumption invariants: PASS.
- `mt5/experts/MentorDeterministicV1EA.mq5` Phase 3A HTF Root OB core drafted.
- Phase 3A compile/smoke verification: pending local MetaEditor/Strategy Tester.
- Child refinement/scenario/order submission remain disabled.

## P1 — Baseline implementation

- [x] Market structure
- [x] Liquidity — Phase 2 core verified
- [ ] Objective selection
- [ ] Root OB — Phase 3A implemented; compile/smoke pending
- [ ] LTF refinement
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