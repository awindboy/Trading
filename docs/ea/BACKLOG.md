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

- Phase 1.1 structure/bootstrap smoke test: PASS.
- Causal log audit: PASS.
- Phase 1.1 bootstrap `STRUCTURE_STATE` over-logging: fixed in Phase 2.
- `mt5/experts/MentorDeterministicV1EA.mq5` Phase 2 liquidity/sweep core drafted.
- Phase 2 compile verification: pending local MetaEditor.
- Trading/order submission remains intentionally disabled.

## P1 — Baseline implementation

- [x] Market structure
- [ ] Liquidity — Phase 2 core implemented; compile/smoke pending
- [ ] Objective selection
- [ ] Root OB
- [ ] LTF refinement
- [ ] Source touch
- [ ] Sweep — physical detector implemented; compile/smoke pending
- [ ] M1 CHoCH
- [ ] Entry
- [ ] SL
- [ ] TP
- [ ] Pending cancellation
- [ ] H4 long-horizon liquidity index — implemented; compile/smoke pending
- [ ] Hierarchical bootstrap / working-set pruning
- [ ] Managed scenario/exposure identity by symbol + magic
- [ ] Minimum-volume parity sizing
- [x] Same-timestamp MTF processing order
- [ ] OnTradeTransaction ticket/history reconciliation

## P2 — Validation

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