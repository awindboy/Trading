# V2 Backlog

Last updated: 2026-08-23  
Current phase: `D-154N PENDING-TO-FILL QUOTE-SIDE DELAY / DEPTH AUDIT`  
2021: `KEEP UNTOUCHED`

## P0 — Foundation

- [x] V1 frozen; V2 continuation-only.
- [x] D151 exact Fill->+1R / SL-first causal platform.
- [x] D153 real-tick batch automation.
- [x] Entry, winner continuation, exit and exposure kept separate.

## P0 — Entry-survival research completed

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
- [x] D154K GOLD25/CADJPY25 cross-scale contrast completed.
- [x] D154L cost-scale transfer validation completed.

## P0 — D154K/L retained finding

- [x] 2025 market ordering: spread/reactionTR GOLD < BTC < SILVER < CADJPY.
- [x] 2025 survival ordering: GOLD > BTC > SILVER > CADJPY.
- [x] Cross-market cost-scale mechanism supported.
- [x] Per-trade spread threshold not supported.
- [x] Universal year/regime determinant not established.

## P0 — D154M

- [x] Apply `2.11R0L11`.
- [x] Compile exact runner-selected terminal MQ5 with 0 errors.
- [x] Verify runner EX5 SHA changed.
- [x] GOLD/CADJPY Q1 D154M OFF/ON canonical parity PASS.
- [x] Require D154M Fill count == pair outcome count.
- [x] Require zero D154M integrity warnings.
- [x] Run GOLD23/GOLD24/GOLD25/BTC25/SILVER25/CADJPY25.
- [x] Report actual WR vs entry-side-quote shadow WR.
- [x] Report `ACTUAL_SL_TO_SHADOW_PLUS_1R` by market/direction.
- [x] Reject any `ACTUAL_PLUS_1R_TO_SHADOW_SL` as instrumentation integrity failure.
- [ ] Do not fit a spread threshold from D154M.

## P1 — after D154M

If friction flips scale monotonically with D154L:
- preregister a separate execution-design hypothesis before strategy changes.

If flips are small:
- retain cost-scale as environment viability correlation but return to non-cost market-regime causes for Entry survival.

## P1 — winner continuation / exit

- [ ] Keep M30 +1R maturity separate from Entry research.
- [ ] Keep V3E provisional until broad strategy-level validation.
- [ ] Revisit exposure only after Entry mechanism is better understood.


## P0 — D154N pending-to-Fill quote-side delay/depth

- [ ] Shadow-only instrumentation.
- [ ] Freeze pending Entry/FVG/Root/SL at accepted pending placement.
- [ ] Record first opposite-quote Entry touch and first executable-quote Entry touch.
- [ ] Measure touch->Fill delay/depth and normalize by FVG/risk.
- [ ] GOLD/CADJPY Q1 OFF/ON parity before evidence.
- [ ] Compare GOLD25/BTC25/SILVER25/CADJPY25 with LONG/SHORT preserved.
- [ ] Do not fit pending offsets or spread thresholds.
