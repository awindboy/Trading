# V3 Backlog

Status: `ACTIVE`

## P0 — V3-001 raw-data bootstrap

- [x] Freeze V3 research purpose and authority boundary.
- [x] Preserve V1/V2 as controls rather than rewriting history.
- [x] Freeze 2023-2025 as initial discovery data.
- [x] Reserve 2022 as V3 validation vault.
- [x] Keep 2021 untouched.
- [ ] Receive GOLD# 2023-2025 M1 CSV.
- [ ] Validate data coverage, duplicates, gaps, order, spread and precision.
- [ ] Record exact broker/server identity and symbol specification.
- [ ] Build deterministic M1 -> M5/M15/M30/H1/H4 aggregator.
- [ ] Prove bar aggregation against MT5 samples.
- [ ] Build reusable experiment registry.

## P0 — common opportunity universe

- [ ] Implement multiple swing detectors as independent named families.
- [ ] Implement external/internal structure representation.
- [ ] Implement liquidity pool candidate families.
- [ ] Implement zone/FVG/OB candidate families.
- [ ] Implement sweep candidates.
- [ ] Implement local M1/M5 structure-transition candidates.
- [ ] Implement FVG first-retest candidates.
- [ ] Deduplicate correlated scenario fan-out into physical opportunities.
- [ ] Produce annual opportunity-density census for 2023/2024/2025.

## P1 — strategy-family experiments

- [ ] Current V2 chain offline reproduction control.
- [ ] Local-live-swing trigger family.
- [ ] M5/M1 adaptive trigger family.
- [ ] Alternative wave detector family.
- [ ] Expanded liquidity family study.
- [ ] Continuation-only vs reversal vs internal-rotation as separate protocols.
- [ ] FVG selector study: widest / first / nearest / Root-proximal.
- [ ] Session/retest interaction.
- [ ] Natural structural parameter stability analysis.
- [ ] Leave-year-out validation inside discovery panel.

## P1 — feature discovery

- [ ] Build outcome-blind pre-entry feature table.
- [ ] Standardized Fill->+1R/SL labels.
- [ ] MFE/MAE path labels.
- [ ] Regularized linear baseline.
- [ ] Tree/boosting discovery model.
- [ ] Interaction/stability analysis.
- [ ] Distill robust model relationships into interpretable candidate rules.
- [ ] Do not promote a black-box live model by default.

## P2 — exact tick layer

- [ ] Request tick data only for surviving candidate families.
- [ ] Exact same-bar event ordering.
- [ ] Bid/Ask barrier race.
- [ ] Dynamic spread replay.
- [ ] Pending-order fill semantics.
- [ ] Compare fast M1 approximation vs exact tick outcome.

## P2 — independent validation

- [ ] Freeze final candidates before opening 2022.
- [ ] Run 2022 once under frozen definitions.
- [ ] Reject rather than retune failed candidates.
- [ ] Keep 2021 untouched.

## P3 — MT5 promotion

- [ ] Reproduce surviving offline candidate in MT5 Strategy Tester.
- [ ] Require exact real-tick execution integrity.
- [ ] Compare against V2 control.
- [ ] Only then implement/branch a V3 EA.

## V3-003 ??GOLD auction-state reconstruction

### P0 ??state engine

- [ ] Build trailing-only normalized state descriptors.
- [ ] Build causal compression/expansion/reload/exhaustion state representation.
- [ ] Preserve state-transition history without look-ahead.
- [ ] Compare strong/weak-period state composition without creating quarter vetoes.
- [ ] Add naive-control harness to every strategy module.

### P0 ??continuation module

- [ ] Re-express the current selective continuation family as an EXPANSION/RELOAD module.
- [ ] Remove mandatory FVG-retest Entry authority from the active hypothesis.
- [ ] Preserve FVG only as a displacement/context candidate until independently justified.
- [ ] Compare trigger-close / simple pullback execution under the same state.
- [ ] Measure full MFE/MAE path, not only +1R survival.

### P0 ??exhaustion reversal

- [ ] Define objective-delivery / near-delivery state causally.
- [ ] Detect failed continuation / opposite acceptance.
- [ ] Build reversal only inside an exhaustion/failed-auction state.
- [ ] Compare against forced-mirror reversal control.

### P1 ??compression breakout

- [ ] Build causal compression state.
- [ ] Require destination-compatible expansion / acceptance.
- [ ] Compare against generic range-breakout control.

### P1 ??portfolio

- [ ] Evaluate modules independently.
- [ ] Verify opportunity populations are physically deduplicated.
- [ ] Combine only after each module has standalone evidence.
- [ ] Evaluate WR, avg winner, expectancy, DD, streaks and state dependence.

### Governance

- [x] Stop trade-level ML winner/loser mining after cross-year failure.
- [x] Stop fixed momentum-horizon search after leave-year-out instability.
- [x] Demote mandatory FVG-retest Entry after direct falsification.
- [x] Adopt L1 -> L2 -> L3 escalation rule.
- [x] Keep GOLD as the active V3 market.
- [ ] Do not open 2022.
- [ ] Keep 2021 untouched.

