# V8-C LONG Exit / Winner-Continuation Research Plan — 2026-09-01

Status: `PREDECLARED ACTIVE RESEARCH PLAN`
Production authority: `NONE`
Entry authority: `V8-C LONG R0.4 PROVISIONAL FROZEN`
Reserve: `GOLD# 2021 LOCKED`

## 1. Objective
The accepted V8-C LONG entry has real-tick open-development evidence near 60% WR, but current TP/SL +/-10 was intentionally an entry-edge validator. The final strategy still needs average winner/payoff meaningfully above 1R while retaining WR>=50% and positive cost-adjusted expectancy.

## 2. Population
Use the exact accepted R0.4 LONG population: 2024 N152, 2025 N165, 2026 N139, total N456. Do not regenerate entries with new filters. Verify exact signal timestamps, actual fills, SL/TP and current exit outcomes before economics.

## 3. All-trade path ledger
For every trade record entry-to-current-exit MFE/MAE, time to MFE/MAE, resolution time, first +0.5R/+1R and -0.5R/-1R timestamps where reached. Keep 1R=$10 for this audit.

## 4. Post-1R continuation shadow ledger
For every trade that first reaches +1R, continue observing the market path as a counterfactual shadow study. Record +1.25R/+1.5R/+2R/+3R first reach, MFE, maximum retracement after +1R before each extension, whether +0.75R/+0.5R/0R was touched first, time-to-extension and right-censoring.

Predeclare diagnostic post-1R horizons: 15m, 30m, 60m, 120m, 240m, 480m. Do not select a favorable horizon from 2025/2026 before the exit family is frozen.

## 5. Do not infer continuation from holding time
Median holding compressed from about 279m to 56m to 15m from 2024 to 2026, but this does not prove spike/reversal because the target remained fixed at $10 while GOLD scale changed. Continuation must be measured directly.

## 6. Discovery / validation order
```text
2024 = exit discovery only
freeze a small candidate family
2025 = validation 1
2026 = validation 2
2021 = locked reserve
```
Do not inspect 2025/2026 post-1R continuation before the initial family is frozen from 2024.

## 7. First mechanical exit family
Control E0: 100% at +1R, SL -1R.

E1: 50% at +1R, 50% at +1.5R.

E2: 50% at +1R, 50% at +2R.

E3: 50% at +1R, runner stop to breakeven only after first +1R, runner target +2R.

E4: 50% at +1R, runner uses one predeclared fixed-distance trailing stop after +1R. If a trailing distance is chosen, choose it from 2024 discovery and freeze before validation; do not dense-grid optimize.

Do not start with indicator-conditioned exits.

## 8. Metrics
Per year and validated pooled result report N, realized WR, average winner/loser R, expectancy R/trade, PF, closed-trade DD, max loss streak, median and 95th percentile holding, runner contribution, top-5/top-10 trade P/L concentration, spread/commission/swap/slippage where available.

## 9. Promotion criterion
```text
realized WR >=50%
average winner meaningfully >1R
cost-adjusted expectancy clearly >0
stable validation years
acceptable DD/loss streak
no tiny-number large-winner dependence
```
Nominal 2R is not success if realized expectancy worsens.

## 10. Conditional runner — later only
Only if a simple runner survives, separately test V8-A/A2 P/R after +1R, probability-candle persistence, time-to-1R, session and simple M5 continuation structure. These variables may not alter the frozen entry population.

## 11. Prohibitions
No new LONG entry filter; no future bars in exit logic; no treating post-exit shadow path as live information early; no forced classification of censored paths; no 2025/2026 threshold rescue; no 2021 use during initial exit discovery; no mixing fresh75 direction evidence into V8-C exit evidence.
