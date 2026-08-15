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

- `mt5/experts/MentorDeterministicV1EA.mq5` Phase 1 structure/bootstrap core drafted.
- Compile verification: pending local MetaEditor.
- Trading/order submission: intentionally disabled in Phase 1.
- Do not mark Market structure or bootstrap items complete until compile + short tester log inspection passes.

## P1 — Baseline implementation

- [ ] Market structure
- [ ] Liquidity
- [ ] Objective selection
- [ ] Root OB
- [ ] LTF refinement
- [ ] Source touch
- [ ] Sweep
- [ ] M1 CHoCH
- [ ] Entry
- [ ] SL
- [ ] TP
- [ ] Pending cancellation
- [ ] H4 long-horizon liquidity index
- [ ] Hierarchical bootstrap / working-set pruning
- [ ] Managed scenario/exposure identity by symbol + magic
- [ ] Minimum-volume parity sizing
- [ ] Same-timestamp MTF processing order
- [ ] OnTradeTransaction ticket/history reconciliation

## P2 — Validation

- [ ] Compile with zero errors
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