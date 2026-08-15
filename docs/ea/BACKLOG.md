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

- `mt5/experts/MentorDeterministicV1EA.mq5` Phase 1 compiled locally: `0 errors / 1 warning / 482 ms / AVX2 + FMA3`.
- Exact Phase 1 warning text was not preserved.
- Phase 1.1 corrects frozen-spec/session/cursor defects found in post-compile review.
- Trading/order submission remains intentionally disabled.
- Market structure stays incomplete until Phase 1.1 recompile + short Strategy Tester log inspection passes.

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