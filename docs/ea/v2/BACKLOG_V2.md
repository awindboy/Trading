# V2 Backlog

Last updated: 2026-08-24  
Current phase: `D-154P LOW-FRICTION PRE-FILL PATH-QUALITY DISCOVERY`  
2021: `KEEP UNTOUCHED`

## P0 ??Foundation

- [x] V1 frozen; V2 continuation-only.
- [x] D151 exact Fill->+1R / SL-first causal platform.
- [x] D153 real-tick batch automation.
- [x] Entry, continuation, exit, execution, market-universe and exposure questions kept separate.

## P0 ??Entry-survival research completed

- [x] D148 failure taxonomy.
- [x] D149 EM not a general Entry solution.
- [x] D154A Fill-time M1 maturity rejected.
- [x] D154B delayed SAME INITIAL_BOS rejected.
- [x] D154C fresh-FVG replacement rejected.
- [x] D154D new-Root rescue failed OOS.
- [x] D154F M1 causal lineage / transition veto not promoted.
- [x] D154G stale prior-owner Root had zero coverage.
- [x] D154G same-owner BOS refresh failed validation.
- [x] Static H1/M30 alignment demoted.
- [x] D154H ordered HTF replay completed.
- [x] D154I post-contact HTF BOS veto failed validation.
- [x] D154J simple HTF exhaustion explanation rejected.
- [x] D154K cross-scale execution contrast completed.
- [x] D154L cost-scale transfer validation completed.
- [x] D154M post-Fill quote-side counterfactual completed.
- [x] D154UL Ultra Low natural experiment completed.

## P0 ??retained execution findings

- [x] Relative execution friction is a supported cross-market mechanism.
- [x] D154M establishes a direct causal post-Fill quote-side component.
- [x] Ultra Low materially reduces spread/reactionTR, spread/R and spread/FVG.
- [x] Ultra Low reduces D154M quote-side flips.
- [x] Ultra Low does not solve SILVER#/CADJPY# Entry survival.
- [x] Per-trade spread threshold remains unsupported.
- [x] Strategy baseline remains unchanged.

## P0 ??D154O Stage A: broad market raw screen

- [x] User provides broad XM Ultra Low symbol list.
- [x] Confirm exact symbol suffixes/names for the primary universe.
- [x] Exclude the initially considered US Stocks cohort before outcomes because `Stocks/US` has no Ultra Low classification.
- [x] Freeze primary Stage-A universe: 32 symbols = 15 Forex + 8 Crypto + 9 Spot Metals.
- [x] Save candidate-universe manifest as `D154O_STAGE_A_UNIVERSE_MANIFEST.md` and `config/d154o_stage_a_universe.json`.
- [x] Prepare standalone automated fixed-week M1+spread+symbol-metadata export workflow; no EA strategy modification.
- [ ] Compile/install `D154OStageAExporter.mq5` in the exact active XM MT5 terminal with 0 errors.
- [ ] Freeze screen window `2026-08-17 .. 2026-08-23` in broker/server time.
- [ ] Include GOLD# same-week reference data.
- [ ] Collect all 32 supplied symbols before interpreting/ranking.
- [ ] Require exporter completion status 32/32 and Ultra Low broker path confirmation.
- [ ] Calculate raw spread/M1-TR proxy.
- [ ] Calculate generic all-M1-FVG spread/width proxy.
- [ ] Calculate spread bps.
- [ ] Record day-level distributions and data quality.
- [ ] Mark inadequate datasets `INSUFFICIENT_DATA`.
- [ ] Do not inspect/run new-symbol one-year performance.
- [ ] Produce full-universe screen table and result ZIP.

## P0 ??D154O shortlist freeze

- [x] Define Gold-like shortlist from Stage-A metrics only.
- [x] Do not use strategy outcome to choose threshold/rank.
- [x] Save shortlist manifest with exact selection rationale.
- [x] Freeze 2-4 non-Gold-like negative controls if practical.
- [x] Prefer some asset-class-matched controls where practical.
- [x] Freeze all Stage-B symbols before any one-year result.

## P0 ??D154O Stage B: 2025 strategy confirmation

- [ ] Run Ultra Low 2025 Every-tick-real-ticks for frozen Gold-like candidates.
- [ ] Run frozen negative controls.
- [ ] D151/D154K/D154M enabled; no new Entry gate.
- [ ] Report Fill count and censoring.
- [ ] Report Fill->+1R survival overall and LONG/SHORT.
- [ ] Report exact spread/reactionTR, spread/R, spread/selected-FVG.
- [ ] Report D154M actual/shadow survival and quote flips.
- [ ] Report realized V3E WR, avg winner R and expectancy separately.
- [ ] Mark tiny strategy populations `INSUFFICIENT_STRATEGY_SAMPLE`.
- [ ] Do not add/drop markets after outcome is known.

## P1 ??temporal confirmation if D154O succeeds

- [ ] Freeze the supported market-selection logic.
- [ ] Use an additional disjoint year where available.
- [ ] Reject permanent market eligibility if the relationship reverses.
- [ ] Only after temporal confirmation consider a production market-eligibility layer.

## P2 ??D154N deferred

- [ ] Pending->opposite quote->executable quote->Fill audit remains documented.
- [ ] Do not implement while D154O is active.
- [ ] Resume only if D154O fails to produce a robust compatible market cohort or later evidence specifically requires it.

## P1 ??winner continuation / exit

- [ ] Keep M30 +1R maturity separate from Entry/market eligibility.
- [ ] Keep V3E provisional until broad strategy-level validation.
- [ ] Revisit exposure only after the compatible market universe is better understood.


## P0 ??D154O Stage B execution package

- [x] Stage-A result accepted with minor crypto-tail truncation note.
- [x] Frozen Stage-B manifest created before new outcomes.
- [x] Frozen cohort = 1 reference + 7 Gold-like + 4 controls.
- [x] Stage-B batch/summary tool prepared.
- [ ] Run `python tools\run_d154o_stage_b_2025.py`.
- [ ] Upload and interpret `D154O_STAGE_B_2025_RESULT.zip`.
- [ ] Do not modify cohort after results.


## P0 ??D154O closeout

- [x] Run frozen 12-symbol Stage-B batch.
- [x] Verify D151/K/M populations for all symbols.
- [x] Mark GBPUSD# `EXECUTION_INVALID`; do not replace frozen control.
- [x] Report Fill->+1R and direction splits.
- [x] Report exact D154K and D154M evidence.
- [x] Mark <20-fill markets insufficient.
- [x] Classify D154O as Outcome B.
- [x] Do not create production market eligibility.
- [ ] Exact V3E cost-adjusted economics require a complete partial-deal ledger and remain separate from D154O Entry research.

## P0 ??D154P low-friction path-quality discovery

- [ ] Build a systematic discovery table from existing 2025 D151/D154K/D154M ledgers.
- [ ] Restrict primary discovery to GOLD#, BTCUSD#, XAUEUR#, USDJPY#.
- [ ] Keep small Gold-family samples descriptive only.
- [ ] Keep GBPUSD# excluded from causal outcome analysis because of execution divergence.
- [ ] Preserve market and LONG/SHORT strata.
- [ ] Use threshold-free effect sizes; do not fit a 2025 cutoff.
- [ ] Freeze only causally interpretable candidate relationships.
- [ ] If timing matters, replace wall-clock/session-gap-contaminated seconds with shadow-only active-bar instrumentation.
- [ ] Validate frozen D154P hypotheses on a disjoint year, preferably 2024.
- [ ] Keep 2021 untouched.
- [ ] No Entry change until validation.

## P0 ??D154P R2 2024 validation

- [x] Reclassify 13:00-15:00 as execution-time/retest regime, not authorization-time filter.
- [x] Freeze ROOT_ESCAPE_BAND 0 < g <= 0.5 as primary pre-Fill geometry hypothesis.
- [x] Check leave-one-market-out, direction, quarter, source-TF and merge robustness.
- [x] Confirm high-friction controls do not receive the same geometry benefit.
- [ ] Run unchanged 2024 GOLD#/BTCUSD#/XAUEUR#/USDJPY# validation.
- [ ] Do not tune Root band or session window on 2024.
- [ ] If ROOT_ESCAPE validates, build shadow widest-FVG vs Root-proximal-FVG selector audit.
- [ ] If session effect validates, build session-restricted virtual-pending shadow audit.
- [ ] Keep 2021 untouched.

## P0 ??D155 mentor fidelity / opportunity audit

- [x] Pause additional outcome-conditioned Entry-filter mining.
- [x] Quantify GOLD 2024/2025 funnel and identify Sweep->CHOCH as primary post-contact choke point.
- [x] Identify source tension around hard three-candle wave formalization.
- [ ] Run FULL_AUDIT GOLD# 2024 and 2025 with exact strategy-count parity.
- [ ] Measure same-contact-bar compatible sweep-detector upper bound.
- [ ] Measure M1 INITIAL_BOS/BOS and M5 structure activity in Sweep->no-CHOCH cases.
- [ ] Select the largest mentor-source-supported fidelity discrepancy.
- [ ] Build only one shadow counterfactual at a time.
- [ ] Verify OFF/ON non-interference before profitability analysis.
- [ ] Census INTERNAL_ROTATION only after trigger-stage fidelity is understood.
- [ ] Keep 2021 untouched.
