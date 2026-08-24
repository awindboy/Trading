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
