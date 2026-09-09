# V9 May 2025 Completion and Postmortem

Date: `2026-09-09`
Status: `MAY 2025 COMPLETE / DEVELOPMENT EVIDENCE / NOT INDEPENDENT VALIDATION`
Market: `GOLD#`
Production authority: `NONE`
EA authority: `NONE`

## 1. Completion boundary

Trading decisions were completed through `2025-05-30 09:59`.

A tooling inspection exposed `2025-05-30 10:00~23:57` before causal decisions were made. No trades are backfilled into that interval. The interval is frozen as `CAUSAL-INTEGRITY CONTAMINATED / NO TRADE`.

May therefore ends flat.

## 2. Grandfathered April carry

P038 SHORT:
- April entry: 3326.04
- May prospective protective stop: 3331.29
- May manual campaign-health exit: 2025-05-01 08:59 @ 3236.67
- captured: +89.37 points
- legacy accounting: about +17.02 legacy-R
- MFE through exit: about +19.95 legacy-R
- giveback from MFE: about 2.93 legacy-R

P038 predates May Hard-SL accounting. Do not combine its legacy-R arithmetically with May new-trade Hard-SL R.

## 3. May-new-entry ledger

| Trade | Date | Side | Exit | R | Evidence |
|---|---|---|---|---:|---|
| P039 | 05-01 | SHORT | HARD SL | -1.00R | clean |
| P040 | 05-02 | LONG | HARD SL | -1.00R | clean |
| P041 | 05-02 | SHORT | DESTINATION | +3.18R | clean |
| P042 | 05-06 | SHORT | HARD SL | -1.00R | qualitatively contaminated |
| P043 | 05-07 | SHORT | HARD SL | -1.00R | clean |
| P044 | 05-07 | SHORT | MANUAL STRUCTURAL | -0.57R | clean |
| P045 | 05-08 | SHORT | MANUAL STRUCTURAL | -0.50R | clean |
| P046 | 05-08/09 | SHORT | HARD SL | -1.00R | clean |
| P047 | 05-12 | SHORT | HARD SL | -1.00R | qualitatively contaminated |
| P048 | 05-12 | SHORT | MANUAL STRUCTURAL | -0.24R | qualitatively contaminated |
| P049 | 05-14 | SHORT | MANUAL STRUCTURAL | +0.15R | clean |
| P050 | 05-15 | SHORT | MANUAL STRUCTURAL | -0.69R | clean |
| P051 | 05-16 | SHORT | HARD SL | -1.00R | clean |
| P052 | 05-16 | SHORT | HARD SL | -1.00R | clean |
| P053 | 05-19 | SHORT | DESTINATION | +2.11R | clean |
| P054 | 05-19 | SHORT | HARD SL | -1.00R | clean |
| P055 | 05-20 | SHORT | HARD SL | -1.00R | clean |
| P056 | 05-21 | SHORT | HARD SL | -1.00R | clean |
| P057 | 05-22 | SHORT | HARD SL | -1.00R | clean |
| P058 | 05-22 | SHORT | MANUAL STRUCTURAL | -0.34R | clean |
| P059 | 05-27 | SHORT | DESTINATION | +1.47R | clean |
| P060 | 05-28 | SHORT | MANUAL STRUCTURAL | -0.74R | clean |
| P061 | 05-29 | SHORT | MANUAL STRUCTURAL | +2.47R | clean |
| P062 | 05-29 | SHORT | MANUAL STRUCTURAL | -0.96R | clean |

## 4. Descriptive May-new metrics

- Trades: 24
- Positive: 5
- Loss: 19
- Positive fraction: 20.8%
- Gross positive: +9.38R
- Gross loss: -16.04R
- Net: -6.66R
- Mean: -0.278R/trade
- Average positive: +1.876R
- Average loss: -0.844R
- Gross-positive / gross-loss magnitude ratio: ~0.585
- Longest loss streak: 7 trades, P042-P048, total -5.31R
- Best May-new trade: P041 +3.18R
- Best Parent-Journey capture: P061 +2.47R

These are descriptive price-risk diagnostics, not exact Bid/Ask/slippage-adjusted execution economics.

Exit-type diagnostics:
- Hard SL: 12 trades, -12.00R total
- Destination-resolution: 3 trades, +6.76R total
- Manual structural/campaign-health: 9 trades, -1.42R total

Intended-scale diagnostics:
- Parent-Journey Participation: 10 trades, -3.89R
- Local Bridge: 14 trades, -2.77R

The scale split is descriptive only and is too small/contaminated for rule promotion.

## 5. Data / causal-integrity qualifications

May is not clean independent validation.

Known qualitative contamination:
- 2025-05-05 / 2025-05-06 were already discussed in the retained V9 foundation.
- 2025-05-12 was already listed in prior V9 discovery evidence.
- P042 (May 6), P047 and P048 (May 12) therefore carry qualitative-contamination tags.

Operational causal incidents:
- 2025-05-13: coarse H1 reveal may have skipped an early LONG; no backfill.
- 2025-05-16 13:00-13:59: coarse reveal skipped a lower move; no backfill.
- 2025-05-27 20:00-23:58: exposed in one inspection; no hindsight insertion.
- 2025-05-30 10:00-23:57: exposed during boundary inspection; frozen no-trade.

The clean-tagged subset excluding P042/P047/P048:
- N=21
- Net=-4.42R
- Positive fraction=23.8%
- Mean=-0.210R/trade
- Gross-positive/gross-loss magnitude ratio ~0.680

This does not rescue the May conclusion.

## 6. Research findings

### H1 — Precommitted Hard SL solved the April risk-drift problem operationally

SUPPORTED AS PROCESS CONTROL.

Every new May trade had a frozen pre-entry price stop. Hard-SL exits were exactly -1R in descriptive price accounting. April-style review latency could no longer turn a nominal ~1R thesis into -2R/-4R price loss.

This is a process success, not evidence of positive edge.

### H2 — Child stop and Parent death separation remains necessary

SUPPORTED.

Several stopped Children were followed by later same-direction Parent movement, but the stopped trade was not rescued. Later participation required genuinely new information.

Examples include P043/P044, P047/P048, P051 and later lower episodes, and P061/P062.

The data continue to support:
`invalid Child != invalid Parent`.

### H3 — WHAT IS NEW? improved auditability but is not sufficient for trade quality

SUPPORTED AS DISCIPLINE / NOT AS EDGE.

May contained many periods where same-auction re-entry was deliberately rejected. This likely reduced obvious rapid-fire churn.

However genuinely independent Children still lost frequently. A new lower business + repair failure is not automatically a good trade.

Therefore:
`independent Child` is a necessary reasoning distinction, not a predictive permission rule.

### H4 — Campaign-health management produced useful examples but did not solve giveback

MIXED / HIGH PRIORITY.

Useful prospective examples:
- P038: large carry protected while still capturing most of the journey.
- P061: MFE ~+4.81R -> exit +2.47R after progression failure and adverse settlement.
- P049: MFE ~+1.55R -> +0.15R; later price exceeded the original stop.
- P058: MFE ~+1.96R -> -0.34R after destination-near progression failure.

Important failures/counterexamples:
- P040: MFE ~+2.60R -> -1R.
- P048: MFE ~+2.12R -> -0.24R.
- P050: MFE ~+1.59R -> -0.69R.
- P055: MFE ~+1.46R -> -1R.
- P056: MFE ~+1.32R -> -1R.

Campaign health can identify deterioration, but the trader still often recognized it after substantial giveback. No fixed lock/trailing threshold is justified.

### H5 — H1 Stochastic/EMA remain shadow-only

SUPPORTED AS NON-AUTHORITY.

Strong upward legs repeatedly continued through >80 adverse dead crosses. Oversold golden crosses sometimes accompanied useful deterioration warnings, but price progression/settlement supplied the actual trade evidence.

No indicator exit rule is earned.

### H6 — April convex payoff shape did not reproduce in May-new trades

IMPORTANT NEGATIVE RESULT.

April had several +10R to +24R Parent winners. May-new trades had:
- best overall +3.18R,
- best Parent-Journey capture +2.47R,
- only 5 positives out of 24.

The low hit-rate architecture survived, but the large positive tail did not. Without the tail, the month was -6.66R.

Therefore April's convex payoff shape remains promising consumed evidence, not a stable demonstrated property.

## 7. Main diagnosis

May's primary problem is no longer unbounded loss. It is:

1. too many apparently reasonable Children that do not develop,
2. insufficient separation between a causally independent Child and an economically worthwhile Child,
3. large favorable excursions still being given back,
4. insufficient capture of true Parent-scale winners.

Hard SL improved the denominator. It did not create the numerator.

## 8. Recommended next research direction

Do NOT add:
- wider fixed stops,
- minimum-R filters,
- N-loss cooldown,
- retry limits,
- stochastic/EMA exits,
- fixed BE/partial/trailing rules.

Carry forward three questions:

1. `PITCH QUALITY BEFORE ENTRY`
   - Beyond independence, what market evidence distinguishes a Child likely to progress from one that merely represents another valid-but-low-quality attempt?
   - Compare matched future-hidden Children with similar hard risk but different subsequent progression.

2. `EARLY PROGRESSION FAILURE`
   - Study the first 1-3 M15/H1 reviews after entry.
   - The important variable may be whether the trade demonstrates expected route behavior soon after entry, not an arbitrary R threshold.

3. `CAMPAIGN HEALTH AFTER MATERIAL MFE`
   - Compare P040/P048/P050/P055/P056/P058/P061.
   - Ask which price/settlement changes separated normal pullback from real loss of progression ability.
   - Keep Stochastic/EMA shadow-only.

## 9. May decision

May does NOT pass a strategy-promotion gate.

Retain:
- Hard SL precommitment,
- Parent/Child separation,
- WHAT IS NEW? documentation,
- no-backfill causal discipline,
- H1 campaign-health review,
- indicator shadow instrumentation.

Do not promote:
- any entry pattern,
- any retry rule,
- any indicator rule,
- any profit-lock rule,
- any production EA.

Formalization gate remains CLOSED.
