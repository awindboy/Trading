# V4 Backlog

Status: `ACTIVE`

## V4-000 — bootstrap / governance

- [x] Open a separate V4 AI-native research line.
- [x] Preserve V1/V2/V3 as controls/negative authority rather than rewriting history.
- [x] Freeze the V4 development laboratory.
- [x] Freeze the V4 cross-market validation vault before opening it.
- [x] Keep GOLD# 2021 untouched.
- [x] Define the first model before validation data are supplied.

## V4-001A — causal dataset

- [x] Build per-symbol M1 stores from MT5 exports.
- [x] Infer/verify symbol point precision from explicit config, never from P/L.
- [x] Build completed-bar M5/M30/H4 streams causally.
- [x] Store `available_at = bar_open + timeframe` and window only on `available_at <= decision_time`.
- [x] Build causal EWM volatility and tick-volume normalization.
- [x] Preserve spread as an explicit input and cost field.
- [x] Preserve market staleness/missingness explicitly.
- [x] Build 15-minute decision samples and 15/60/240-minute labels.
- [x] Hash prepared artifacts and write a data manifest.
- [x] Add parity checks for row ordering, duplicates, OHLC validity, decisions and future-label availability.

## V4-001A — baseline controls

- [ ] FLAT control.
- [ ] Always-LONG / always-SHORT diagnostics.
- [ ] 60-minute momentum sign control.
- [ ] 60-minute mean-reversion sign control.
- [x] Causal linear/logistic raw-feature baseline.
- [ ] Record turnover and spread burden for every economic control.

## V4-001A — learned representation

- [ ] Train `V4_001_CausalPatchPolicy` with the frozen config.
- [ ] Use at least 3 fixed seeds; do not select the lucky seed.
- [ ] Report 15/60/240m AUC, correlation, NLL and calibration.
- [ ] Run expanding temporal evaluation.
- [ ] Run leave-one-market-out evaluation.
- [ ] Compare against the same-input linear baseline.
- [ ] Report market/year contribution rather than pooled metrics only.
- [ ] Run target-only vs cross-market-context ablation.
- [ ] Run timeframe ablation only after the base result is recorded.

## Stage-A gate

Progress to the trading controller only if:
- held-out directional skill is above chance with bootstrap uncertainty excluding 0.5 on the pooled held-out sample;
- skill is >0.5 in at least 3 of 4 held-out markets for the primary 15m target;
- the learned model beats the same-input linear baseline in at least 3 of 4 held-out markets;
- calibration is not catastrophically broken;
- the result is not carried by one market/year.

If Stage A fails, do not start RL. Decide whether to expand the information set, change target horizon/problem,
or close the short-horizon directional-learning hypothesis.

## V4-001B — full-information cost-aware controller

Locked until Stage A passes.

- [ ] At each 15m decision choose target exposure `{-1, 0, +1}`.
- [ ] Use predicted next-15m mean return as the state forecast.
- [ ] Charge one-way half-spread for each unit of exposure change.
- [ ] Let FLAT win naturally when expected edge does not pay transition cost.
- [ ] No hand-tuned confidence threshold in the first controller.
- [ ] Report cost-adjusted return, turnover, trade episodes, DD, streaks and contribution.
- [ ] Compare target-only vs cross-market controller.

## V4-001 freeze / external validation

- [ ] Freeze exact code/config/checkpoint selection protocol.
- [ ] Write external validation contract.
- [ ] Only then request/open XAUJPY#/XAUCNH#/GAUCNH#/GAUUSD# 2023-2025.
- [ ] No retuning on external-market validation.
- [ ] Keep GOLD# 2021 untouched.

## V4-002 — sequential control / RL

Deferred until V4-001 establishes information and simple-controller economics.

Possible scope:
- position duration state;
- variable exposure size;
- multi-step utility / distributional critic;
- explicit drawdown/risk constraints;
- partial close / dynamic holding;
- offline-to-simulator RL comparison.

Do not choose PPO/SAC/Decision Transformer in advance. Algorithm selection follows the exact control problem.

## Later execution layer

- [ ] exact tick replay;
- [ ] bid/ask ordering;
- [ ] commission/slippage/swap;
- [ ] MT5 Strategy Tester parity;
- [ ] deployment/inference architecture;
- [ ] live sizing only after all prior gates.

## V4-001 Representation Tournament

### Research expansion / literature
- [x] Perform current web/open-source review before expanding the first neural design.
- [x] Add `V4_LITERATURE_LEDGER.md`.
- [x] Record current Kronos, Fin-JEPA and MOMENT references and provenance caveats.
- [x] Freeze external-pretrained models as diagnostic-only unless provenance becomes pristine.

### R1 supervised claim-grade
- [x] Freeze leakage-safe outer evaluation and strict future-isolated LOMO.
- [x] Freeze seeds 17/29/43 and automatic Stage-A gate.
- [ ] Run all six R1 folds on CUDA.
- [ ] Apply unchanged Stage-A verdict.

### R2 self-supervised claim-grade
- [x] Implement `V4_001_MarketJEPA` without changing the base causal information set.
- [x] Freeze 15m future-latent prediction inside the training allocation.
- [x] Freeze encoder before a linear direction probe.
- [x] Exclude held-out LOMO market from self-supervised pretraining context and targets.
- [x] Use the same R0 comparison and Stage-A gate as R1.
- [ ] Run all six R2 folds on CUDA.
- [ ] Apply unchanged Stage-A verdict.

### Tournament selection
- [x] Freeze PASS-first selector before R1/R2 outcomes.
- [x] Tie-break by median strict-LOMO delta vs R0, then pooled 2025 AUC.
- [ ] Generate `V4_001_TOURNAMENT_SUMMARY.json`.
- [ ] Keep V4-001B/RL locked if neither claim-grade contender passes.

### Transfer diagnostics
- [x] Add pinned Kronos-mini diagnostic runner.
- [x] Add MOMENT-1-small embedding diagnostic runner.
- [ ] Run only if useful after/beside claim-grade tournament; do not use as validation rescue.
