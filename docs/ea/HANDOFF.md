# EA Development Handoff

Last updated: 2026-08-20
Repository base checked before this update: `0d9ca2cc72dceb6e982df4700ee83f42a11135af`
Status: D-135A BUILD 1.91 CONTROL PRESERVED / REGIME RESEARCH V1 FROZEN / DIRECT DEVELOPMENT VALIDATED / 2022 FIRST OOS PASS
Current phase: frozen Regime V1 cross-symbol robustness expansion; multi-symbol risk-sizing harness prepared; 2021 remains the preferred final untouched time-series confirmation
Remaining execution issue: recoverable broker pending-cancel rejection retry remains separate from regime research

## Authority

- `AGENTS.md` remains the highest current baseline strategy authority.
- `docs/ea/EA_SPEC.md` remains the deterministic baseline implementation contract.
- `docs/ea/DECISIONS.md` records design and research-governance decisions.
- `docs/ea/REGIME_RESEARCH_2023_2025.md` preserves the complete regime discovery, failed hypotheses, freeze, direct validation, and first OOS evidence.
- `docs/ea/STRATEGY_RESEARCH_STATE.md` is the compact current research-state summary.
- `docs/ea/TEST_RESULTS.md` is the execution/backtest evidence ledger.
- Regime Research V1 is **not yet promoted into `AGENTS.md` or `EA_SPEC.md`**. OOS PASS is evidence for a later explicit promotion decision, not an automatic authority change.

## Current deterministic control

Build 1.91 remains the control strategy:

```text
H1/M30 map
-> eligible HTF Root OB
-> Root contact
-> direction-compatible M1 liquidity Sweep
-> later M1 protected-break CHoCH
-> causal fresh M1 FVG
-> widest eligible FVG
-> first retest Entry
-> contributor-merged SL/objective geometry
-> hedging same-direction execution
-> pending/fill/cancel/close reconciliation
```

Control properties remain:

```text
SL = ROOT_OB_DISTAL_20
LAST_OPPOSITE_OB + FVG_ORIGIN_OB = baseline Root recognizers
PD Array = context/reference only
same-direction independent add-ons = allowed on hedging accounts
opposite-direction coexistence = blocked
```

## Research protocol

Dataset roles were frozen before 2022 was opened:

```text
2023–2025 = Development / Research
2022      = first sealed OOS
2021      = preferred final untouched confirmation
```

The frozen model was not changed after opening 2022.

## Frozen Regime Research V1

State:

`M30_CLEAN_PERSISTENT_EXPANDING`

Exact definition:

```text
scope = EXTERNAL_CONTINUATION
snapshot = baseline-equivalent scenario PLAN freeze
required context = latest 12 confirmed M30 waves with available_at <= PLAN freeze

persistence:
progression >= 2/3

structural stability:
M30 STRUCTURE_PROTECTED_BREAK inside the same 12-wave span <= 1

expansion:
leg_expansion_ratio > 1.0

leg_expansion_ratio =
mean(abs(last 4 M30 wave-to-wave legs))
/
mean(abs(previous 4 M30 wave-to-wave legs))
```

State vocabulary remains:

```text
M30_CLEAN_PERSISTENT_EXPANDING
UNKNOWN
```

Do not relabel the complement as BAD and do not add extra thresholds after the OOS result.

## Development-set research result before direct execution

Canonical PLAN-freeze attribution:

### Parent — `M30_CLEAN_PERSISTENT`

```text
39 trades / 15 wins
+52.489559R
mean +1.345886R/trade
Max DD -8.1724R
longest losing streak 8

2023 +47.219207R
2024  +0.685660R
2025  +4.584692R
```

### Frozen V1 — `M30_CLEAN_PERSISTENT_EXPANDING`

```text
20 trades / 13 wins / 65.0%
+53.847843R
mean +2.692392R/trade
Max DD -3.012821R
longest losing streak 3

2023 +43.879687R
2024  +2.363062R
2025  +7.605095R
```

The feature search stopped there. `directional_advance_norm`, weak-progression BAD veto, H1/M30 agreement, PD/location, maturity, overlap/cleanliness thresholds, impulse/retracement quality scoring, EMA/ADX/ATR/RSI, and multi-factor quality scores were not included.

## Direct MT5 research implementation

The research EA was compiled/run as a standalone complete EA and later received logging-only research harness changes.

Current research harness identity:

```text
research family = 1.92R1
logging/baseline-toggle revision = 1.92R1L2
strategy core = D134 execution semantics unchanged
```

ResearchMode options:

```text
V1_REGIME_PARENT_CLEAN_PERSISTENT
V1_REGIME_V1_CLEAN_PERSISTENT_EXPANDING
V1_REGIME_BASELINE_NO_GATE
```

The baseline mode disables only the regime gate; it does not change the original execution chain.

Logging modes:

```text
RESEARCH_COMPACT = default for long runs
FULL_AUDIT       = diagnostic replay
```

The compact logger is logging-only. It retains M30 regime inputs, regime decisions, scenario/execution milestones, broker lifecycle, and divergence/error evidence while suppressing high-volume detector/audit rows.

## Direct Development Set validation — 2023–2025

The original full-audit Expansion run independently reproduced all 2,338 `EXTERNAL_CONTINUATION` regime decisions from M30 wave/PB history with:

```text
progression mismatches = 0
protected-break-count mismatches = 0
leg-expansion mismatches = 0
final PASS/REJECT mismatches = 0
```

Execution divergence was zero.

### Parent direct

```text
46 trades / 15 wins / 32.6%
+45.436530R
mean +0.987751R/trade
Max DD -11.204262R
longest losing streak 11

2023: 23 trades / +45.219207R
2024: 14 trades /  -3.364869R
2025:  9 trades /  +3.582192R
```

### Expansion V1 direct

```text
24 trades / 13 wins / 54.2%
+49.797314R
mean +2.074888R/trade
Max DD -5.173397R
longest losing streak 5

2023: 12 trades / +43.879687R
2024:  7 trades /  -1.687467R
2025:  5 trades /  +7.605095R
```

All 24 Expansion trades are exact members of the Parent run and have identical R. Expansion removes 22 Parent trades:

```text
22 trades / 2 wins
-4.360784R
mean -0.198217R/trade

2023: 11 removed / +1.339520R
2024:  7 removed / -1.677402R
2025:  4 removed / -4.022903R
```

This direct A/B comparison supports expansion as genuinely incremental on the Development Set.

The direct run also proved why post-filtered attribution cannot be the final execution authority. Filtering can alter contributor merge and opposite-direction exposure state, creating or releasing later opportunities. Two additional late-December 2024 positions were also absent from the old calendar-bounded closed-trade attribution because they closed in early 2025. Direct Strategy Tester execution therefore controls final research performance.

## 2022 first OOS — PASS

The frozen OOS contract required:

```text
V1 trades >= 5
Total R > 0
mean R/trade > 0
Max DD less severe than 2022 continuation baseline
longest losing streak no worse than 2022 continuation baseline
```

Direct 2022 results:

| Mode | Trades | Wins | Total R | Mean R | Max DD | Longest loss streak |
|---|---:|---:|---:|---:|---:|---:|
| Baseline `EXTERNAL_CONTINUATION` | 72 | 15 | -14.476581R | -0.201064R | -20.764118R | 18 |
| Parent `M30_CLEAN_PERSISTENT` | 16 | 3 | -3.825354R | -0.239085R | -5.741120R | 5 |
| Frozen Expansion V1 | 6 | 1 | +0.994756R | +0.165793R | -3.012334R | 3 |

The Expansion V1 result satisfies every pre-registered PASS condition.

Expansion also beats the Parent on both required incremental dimensions:

```text
expectancy:
Parent -0.239085R/trade
V1     +0.165793R/trade

drawdown:
Parent -5.741120R
V1     -3.012334R
```

The six Expansion trades are exact members of the Parent run with identical R. Expansion removes ten Parent trades that sum to:

```text
10 trades / 2 wins / -4.820111R
mean -0.482011R/trade
```

Classification:

```text
2022 FIRST OOS = PASS
Expansion incremental support vs Parent = PASS
Frozen definition changed after opening 2022 = NO
```

## OOS caveat

The 2022 Expansion result is positive but small-sample and tail-dependent:

```text
6 trades
1 winner
winner ≈ +6.02R
5 losses ≈ -5.03R combined
net ≈ +0.995R
```

Therefore 2022 is evidence that the frozen gate transferred, not proof that the strategy is fully robust.

## Next actions

1. Preserve the exact frozen V1 definition and thresholds.
2. Use `V1_REGIME_BASELINE_NO_GATE`, Parent, and Expansion modes to run the preferred untouched 2021 confirmation under identical Strategy Tester conditions.
3. Evaluate 2021 without threshold changes and record the result before any promotion decision.
4. If final confirmation remains supportive, make a separate explicit decision on whether the regime gate becomes baseline strategy authority and only then update `AGENTS.md` / `EA_SPEC.md`.
5. If the model is changed after seeing 2022, call it V2; 2022 is no longer OOS for V2.
6. Separately implement exact-ticket retry for recoverable pending-cancel rejection. Do not mix that execution fix into regime-model research.

## Do not do

- Do not tune `leg_expansion_ratio > 1.0` after the 2022 result.
- Do not add a quality score or stack failed Development-Set features.
- Do not reinterpret `UNKNOWN` as automatically BAD.
- Do not promote the research gate into baseline authority merely because 2022 passed.
- Do not use an execution-divergent run as final profitability evidence.

## Prepared multi-symbol position sizing — 1.92R1L3

The research harness now has a prepared execution-only position-sizing extension for cross-symbol testing. It does **not** change Regime V1, Entry, SL, TP, contributor merge, add-on, or exposure semantics.

Tester-selectable sizing modes:

```text
V1_SIZE_MINIMUM_VOLUME_PARITY
V1_SIZE_FIXED_RISK_MONEY
V1_SIZE_EQUITY_PERCENT_RISK
```

Risk-sized modes use MT5 `OrderCalcProfit` on the frozen Entry -> SL geometry to estimate account-currency loss, then normalize volume downward to the symbol's `SYMBOL_VOLUME_MIN / MAX / STEP`. A normalized risk-sized order may under-use the target because of volume granularity but may not exceed the target risk. If the requested risk cannot be represented because it is below minimum or above maximum volume, execution fails closed.

`OrderCalcMargin` is diagnostic only; `OrderCheck` remains the final broker/account execution-feasibility authority. Minimum-volume mode preserves the historical control volume behavior.

Compact logging now retains:

```text
symbol / account currency
sizing mode
equity snapshot
target risk money
raw and normalized volume
planned Entry->SL risk
estimated margin
actual fill->SL risk
entry/exit commission and fee
exit profit / swap
realized net money
```

Prepared build identity:

```text
1.92R1L3
phase = REGIME_RESEARCH_V1_MULTI_SYMBOL_RISK_SIZING
```

Status: **PREPARED / METAEDITOR COMPILE AND SHORT PARITY SMOKE PENDING**. Do not treat D-141 as validated until compile and a minimum-volume parity fixture pass.

Cross-symbol research intent:

- run the frozen Expansion V1 unchanged across roughly ten symbols under one common risk-sizing protocol;
- report symbol-level and pooled R statistics separately from actual portfolio drawdown;
- do not tune Regime thresholds per symbol;
- keep 2021 untouched as the preferred final time-series confirmation for the frozen Gold development lineage.
