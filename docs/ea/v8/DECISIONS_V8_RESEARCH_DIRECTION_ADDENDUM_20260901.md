# V8 Decisions Addendum — Reliability, Fresh75 and Exit Direction — 2026-09-01

This file continues `DECISIONS_V8_A2_ADDENDUM_20260901.md` from D-V8-077 onward.

## D-V8-077 — Retain A2 percentile rank/state as the primary A2 reliability interpretation
Retain prior-288 R15/R30/R60 and EXTREME/HIGH/QUIET states as the primary A2 interpretation. Absolute probability is secondary and regime-dependent. This does not promote A2 over frozen V8-A.

## D-V8-078 — Treat TV79 as separate, never imputed FULL A2
Do not fill missing TradingView volume into FULL A2. `A2-TV79` is a separately retrained 79-feature price-only survival model and remains research/shadow only.

## D-V8-079 — Probability candles are visualization-only
M15+ P15 candles use completed underlying M5 P15 values: O first, H max, L min, C last. No partial current M5. Probability-candle direction is not GOLD direction.

## D-V8-080 — Use session as prior/context, not a hard V8-C filter
Record NY local 08:00-10:30 as the strongest recurring movement window, but do not add NY-only filtering to frozen V8-C LONG. Session overlaps materially with A2 state, especially EXTREME.

## D-V8-081 — Define fresh-P15-75 cross as a separate auto-direction trigger
Retain previous P15<75 and current P15>=75, mandatory direction, next-M5-open. Do not enter on every bar while P15 stays high.

## D-V8-082 — Record broad fresh75 technical tournament as negative evidence against an obvious ~70% solution
Roughly 790 causal technical/MTF/candle/activity features, including creative oscillator-band composites, did not produce a robust ~70% mandatory-direction rule. Best compact development results remained around 59%. This does not prove direction impossible with new information.

## D-V8-083 — Mark 2026 consumed for fresh75 direction research
2026 was repeatedly inspected during the broad tournament. Do not describe it as untouched validation for later fresh75 tick research. Any earlier wording to that effect is superseded. 2021 remains locked.

## D-V8-084 — Change fresh75 follow-up from indicator proliferation to new information sources
If resumed, prioritize raw XM quote microstructure, CME Gold futures centralized order flow, and macro-event surprise/context before arbitrary new technical thresholds.

## D-V8-085 — Make V8-C LONG exit/path audit the primary research direction
The next primary task is winner continuation and final exit architecture for the exact frozen V8-C LONG entry population. Entry already has ~60% real-tick evidence; payoff expansion is still untested.

## D-V8-086 — Do not infer spike-and-reversal from holding-time compression
The 2024~2026 median holding compression does not prove post-TP reversal because the barrier remained a fixed $10 while price/volatility changed. Measure continuation directly.

## D-V8-087 — Audit all 456 LONG trades, not winners only
Reconstruct all accepted R0.4 paths. For +1R winners additionally record +1.25/+1.5/+2/+3R reach, post-1R retracement, time and right-censoring. Winner-only MFE is insufficient.

## D-V8-088 — Separate exit discovery and validation
Use 2024 for exit discovery, then freeze the candidate family before opening 2025 validation and subsequently 2026 validation. Keep 2021 locked.

## D-V8-089 — Start with simple mechanical exit controls
First compare +1R control, partial +1R with +1.5R/+2R runner, partial +1R then BE, and one simple fixed trailing rule. Do not start with indicator-conditioned exits.

## D-V8-090 — Exit promotion requires WR>=50%, winner>1R and positive full-cost expectancy
Also require validation stability, drawdown/loss-streak reporting and no dependence on a few outsized winners.

## D-V8-091 — Keep V8-C entry and exit research separate
No new LONG entry filter may be introduced to rescue an exit variant. R0.4 entry remains the control.

## D-V8-092 — Keep GOLD# 2021 locked through exit discovery
Do not spend 2021 on fresh75 rescue, session filtering or initial exit design. Use it only after a complete architecture is frozen and merits final temporal validation.
