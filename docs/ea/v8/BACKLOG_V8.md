# V8 Backlog

Status date: `2026-09-02`
Active phase: `V8-A-N-SLOW / ONSET + EXTENSION MAPPED / DIRECTION BOTTLENECK`

## Slow scale / probability

- [x] Semantic reset from per-M5 ATR target chasing to slow regime-scale target.
- [x] Identify `0.25 * previous-completed H4 ATR14` as provisional primary candidate.
- [x] Rebuild decision-block H4 alignment and horizon eligibility.
- [x] Reproduce Phase-0 aggregate probability result.
- [x] Build Phase-2 outcome-blind sampling robustness model.
- [x] Quantify fresh-event identity sensitivity: Jaccard 57.22%.
- [ ] Decide/freeze final training architecture: full vs explicitly de-overlapped.
- [ ] Build final reproducible official Slow-N P15/P30/P60 pack.
- [ ] Calibration/logloss/decile/month/quarter stress before final probability authority.
- [ ] Keep multiplier selection independent of direction/P&L.


## Higher-horizon EXTENSION

- [x] Predeclare `H={60,120,240}m x k={0.50,0.75,1.00} H4 ATR` movement-only screen.
- [x] Confirm annual target base-rate stability across 2022-2026.
- [x] Retain `0.75 * previous-completed H4 ATR14` as extension research target.
- [x] Build joint 4-class `P60/P120/P240` survival surface with structural horizon monotonicity.
- [x] Run Phase-0 and Phase-2 de-overlap robustness.
- [x] Quantify P60/P120/P240 AUC / calibration / fresh75 realization.
- [x] Measure Phase-0/Phase-2 extension-fresh Jaccard.
- [x] Show current ONSET fresh predicts 0.50/60, 0.75/120, 1.00/240 larger moves at ~2-3x unconditional base rate.
- [x] Test direct P_UP/P_DOWN on higher-horizon fresh: failed.
- [x] Build signed M1/M5 multi-horizon direction representation: failed to transfer.
- [x] Reject “longer horizon solves direction” without threshold rescue.
- [x] Keep `P120 @ 0.75 H4 ATR` as central extension research coordinate.
- [ ] Do not freeze an EXT fresh trigger yet.
- [ ] Do not use EXT as an entry veto for the mandatory-fresh objective.
- [ ] After direction freeze, preregister EXT-conditioned holding/runner/target research.
- [ ] Build final ONSET+EXT probability model pack only after training architecture freeze.

## Direction transfer — completed negatives

- [x] Legacy deterministic 7-voter transfer: failed.
- [x] M5 Stoch standalone: failed.
- [x] Market-question equal panel: failed.
- [x] Immediate pressure: failed.
- [x] Oscillator transition: failed.
- [x] M15/H1/H4 structure standalone: failed.
- [x] HTF regime: failed.
- [x] Volatility transition: failed.
- [x] Location/liquidity: failed.
- [x] M1 tape proxy: failed.
- [x] M1 recent direction: failed.
- [x] M1 pressure: failed.
- [x] M1 Stoch standalone: failed.
- [x] M1 EMA3/8 standalone: failed.
- [x] Old asymmetric MTF state: failed/reversed.
- [x] BB-A transfer: failed.
- [x] BB-C transfer: failed/reversed in 2026.
- [x] BB-D transfer: failed.
- [x] Generic tick majority on available overlap: failed.
- [x] Generic higher-horizon P_UP/P_DOWN: failed.
- [x] Signed higher-horizon M1/M5 path direction: failed.

Do not rescue these with threshold or weight searches.

## Direction transfer — retained candidates

### BB-B
- [x] Phase-0 n=5 transfer.
- [x] Phase-2 n=5 transfer.
- [x] n=3/5/8 robustness across both phases.
- [x] All 18 year x phase x window cells >50%.
- [ ] Quarter/month stress.
- [ ] Near-miss state comparison.
- [ ] Interaction with Stoch/M1/tick without arbitrary search.

### Stoch/M1/tick temporal re-synchronization
- [x] Test `relative 0001` on old/new event overlap.
- [x] Test -10m shifted placebo on overlap.
- [x] Check M1 recent counter-move.
- [x] Check M1 Stoch alignment/3m transition as tiny nested diagnostics.
- [ ] Extract raw ticks for every new Slow-N fresh75 decision.
- [ ] Re-run aligned/placebo `0001` on full coverage.
- [ ] Re-run M1 Stoch transition on full coverage.
- [ ] Family-wise permutation audit after full transfer.

## M1 structure

- [x] Detect reproducibility gap in old confirmed-structure generator.
- [ ] Recover original generator or explicitly freeze a new definition.
- [ ] Require parity test before using as a confidence layer.

## Path Clearance

- [ ] Rebuild natively using Slow-N target geometry.
- [ ] Retest old `1110` old-flow anti-edge.
- [ ] Compare against BB-B/new-flow temporal states.

## MT5 indicator

- [x] Preserve legacy `V8ANP15ContextIndicator.mq5` as M5-A-N historical indicator.
- [x] Add `V8SlowNP15ContextIndicator.mq5` for Phase-0 Slow-N chart inspection.
- [x] Embed Phase-0 scaler/4-class coefficients.
- [x] H4 decision-block target alignment.
- [x] Adjustable P15 threshold drives both horizontal line and main-chart marker.
- [x] H4 ATR rank + MA20-distance/SlowTarget rank in same 0-100 panel.
- [x] Create Python/MQL reference points.
- [ ] Local MetaEditor compile.
- [ ] Python/MQL live parity audit on references.
- [ ] Replace probe model only when final Slow-N model is frozen.

## Economics / execution

- [ ] Keep exits closed until Slow-N direction is frozen.
- [ ] Pre-register payoff family.
- [ ] Define whether entry-time H4 scale remains frozen for the entire trade.
- [ ] MT5 Every Tick based on real ticks.
- [ ] Full costs: spread/slippage/commission/swap as applicable.
- [ ] WR / avg winner / EV / PF / DD / loss streak / big-winner dependence.

## Evidence discipline

- [x] 2022-2026 consumed development evidence.
- [ ] GOLD# 2021 remains locked.
