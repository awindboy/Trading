# V8 Backlog

Status date: `2026-09-02`
Active phase: `V8-A-N SLOW-SCALE FORMALIZATION / LEGACY DOWNSTREAM REVALIDATION PENDING`

## Authority reset
- [x] Identify mismatch between intended meaningful-move normalization and per-M5 ATR target chasing.
- [x] Reclassify old `1.50*M5 ATR fresh75` N1 as legacy M5-relative research, not active Slow-N authority.
- [x] Preserve old results as historical evidence rather than deleting/relabeling them as invalid.
- [x] Mark all old downstream direction/M1/tick/Bollinger/economic results as requiring Slow-N revalidation.
- [x] Keep GOLD# 2021 locked.

## Slow-scale target research
- [x] Compare target update cadence for M5/H1/H4/D1 ATR scales.
- [x] Build initial H1/H4/D1 target-size and 15m base-rate diagnostics.
- [x] Identify `0.25 * previous-completed H4 ATR14` as provisional primary balance candidate.
- [x] Confirm 2022-2026 H4 target base rate is roughly stable (~20.7-22.8%).
- [x] Confirm 2026 median H4 target is ~10.1p.
- [x] Identify D1 as potentially too slow from quarterly difficulty drift.
- [ ] Rebuild exact full causal H1/H4/D1 bars with explicit block-boundary unit tests.
- [ ] Verify no partial H4/D1 candle enters target scale.
- [ ] Stress H4 target constancy, gaps/weekends, DST/server-time effects and missing bars.
- [ ] Freeze final slow scale before direction research.
- [ ] Do not optimize H4 multiplier from direction/P&L.

## Slow-N probability model
- [x] Lightweight 86-feature survival probe for fixed10/M5/H1/H4/D1 target families.
- [x] H4 probe annual fresh75 ~78.55 / 78.53 / 76.47%.
- [x] 25-minute training-phase sensitivity check.
- [ ] Decide full-training vs explicitly de-overlapped training architecture before final pack.
- [ ] Rebuild formal P15/P30/P60 model with strict 60m purge.
- [ ] Report AUC/Brier/logloss/calibration/deciles by year and quarter.
- [ ] Enforce/check horizon monotonicity.
- [ ] Build reproducible model/manifest pack.
- [ ] Python/MQL parity before any MT5 authority.

## New Slow-N N1
- [ ] Profile P15>=75 without direction labels.
- [ ] Profile fresh75 without direction labels.
- [ ] Annual/monthly/quarterly movement realization.
- [ ] Active-day frequency and trigger spacing.
- [ ] H4-block clustering / repeat-trigger rate.
- [ ] Session distribution.
- [ ] actual target-distance distribution.
- [ ] Freeze N1 before opening downstream direction outcomes.

## Legacy chart-direction transfer tests
- [ ] Re-run semantic deterministic 7-voter panel unchanged where possible.
- [ ] Re-run MTF expansions / market-question panel as negative controls.
- [ ] Re-run M5 Stochastic direction.
- [ ] Re-run causal M15/M30/H1/H4 structure states.
- [ ] Re-run Path Clearance states.
- [ ] Do not threshold-rescue failed transfers.

## M1 transfer tests
- [ ] Re-run M1 recent direction / pressure / causal confirmed structure.
- [ ] Re-run M1 sweep/reclaim / M1 Stoch / EMA3-8 context.
- [ ] Test M1 structure agreement as a confidence layer.
- [ ] Re-run M5 Stoch -> M1 counter-move -> M1 oscillator transition sequence.

## Raw tick transfer tests
- [x] Preserve V4 UTC-wall-clock alignment method; V1/V2/V3 remain invalid.
- [ ] Rebuild exact V4 aligned and -10m placebo windows for new N1 decisions.
- [ ] Re-run unique tick4 `[NET,MOVE,CLV,RUN]` panel as negative control.
- [ ] Pre-register and test old relative `0001` Stoch/tick re-synchronization rule unchanged.
- [ ] Re-run M1-Stoch + relative `0001` interaction.
- [ ] Re-run Path relative `1110` anti-edge and near-miss states.
- [ ] Family-wise permutation audit after fixed transfer family is evaluated.

## Bollinger(20,2) transfer tests
- [ ] Re-run state representation using primary 5 prior M5 bars + trigger; n=3/8 robustness only.
- [ ] BB-A middle residence -> near lower inside.
- [ ] BB-B middle residence -> above upper + abs SMA gap widening.
- [ ] BB-C inside + gap shifts down + >=2 center crosses.
- [ ] BB-D middle residence + bandwidth contraction + exactly 1 center cross.
- [ ] Do not convert Bollinger components into generic independent voters.
- [ ] Re-run multiplicity audit.

## Direction authority
- [ ] Treat exact old N2-R1 only as a legacy diagnostic because it contains old M5-A-N probability semantics.
- [ ] Build any native Slow-N direction rule only after fixed transfer tests.
- [ ] Separate discovery and validation; 2022-2026 remain consumed.
- [ ] Do not use 2021 for direction discovery.

## Economics / execution
- [ ] Keep N3 closed until Slow-N direction is frozen.
- [ ] Pre-register Slow-N-consistent risk/payoff family before opening results.
- [ ] Define whether trade risk/target remains frozen from entry H4 block for the full trade.
- [ ] MT5 Every Tick based on real ticks.
- [ ] Include spread, slippage, commission and swap where applicable.
- [ ] Report WR, avg winner/loser R, EV, PF, DD, loss streak, holding time and big-winner dependence.

## Controls / other branches
- [x] V8-A absolute-$10 control preserved.
- [x] V8-A2 preserved.
- [x] fixed-$10 $10/$13 remains historical complete development benchmark.
- [x] V8-C kept separate.

## Reserve
- [x] 2022-2026 = consumed/open development evidence.
- [ ] GOLD# 2021 remains locked until a complete Slow-N architecture genuinely merits reserve validation.
