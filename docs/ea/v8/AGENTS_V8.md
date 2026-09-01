# V8 Research Instructions

Status: `ACTIVE`
Generation: `V8`
Last synchronized: `2026-09-01`
Production authority: `NONE`
Market: `GOLD#`
Untouched reserve: `GOLD# 2021`

## 1. Current branch map

```text
V8-A MOVEMENT PROBABILITY
FROZEN / RETAINED / CURRENT MOVEMENT CONTROL

V8-A2 MOVEMENT CHALLENGER
RESEARCH COMPLETE / RETAINED / NOT PROMOTED
relative-rank reliability layer retained
TradingView TV79 price-only fallback = research/shadow only

V8-B LEARNED DIRECTION
PAUSED / NEGATIVE-RESULT AUTHORITY

V8-C LONG ENTRY
PROVISIONAL FROZEN
MT5 Every Tick based on real ticks verified on open-development evidence

V8-C-S1 SHORT ENTRY
RESEARCH-ONLY / M1 PROXY

FRESH75 AUTO-DIRECTION
SEPARATE RESEARCH TRACK / NO AUTHORITY
broad technical-indicator search completed without a robust ~70% direction result

V8-C EXIT / WINNER CONTINUATION
CURRENT PRIMARY RESEARCH DIRECTION
```

Research EA authority remains `V8MAMTFStochResearchEA R0.4` for frozen V8-C LONG validation only.

## 2. Frozen V8-A contract

```text
C0 = completed causal decision price
barrier = +/-10 GOLD price units
H = 15m / 30m / 60m
53-feature causal M1 movement representation
2024 <- 2022-2023
2025 <- 2022-2024
2026 <- 2022-2025
```

V8-A predicts movement, not direction. Do not modify it to rescue direction, entry, exit, execution, session or market-suitability results.

## 3. V8-A2 retained research state

Retained A2:

```text
53 original movement features
+ 33 barrier-difficulty/regime features
+ four-class first-hit-time survival target
class0 <=15m
class1 15-30m
class2 30-60m
class3 no hit by 60m
P15 = class0
P30 = class0+class1
P60 = class0+class1+class2
```

For every output, training eligibility requires:

`decision_time + 60m <= evaluation boundary`.

Strict outer AUC:

```text
          2024     2025     2026
P15     0.8660   0.8736   0.8190
P30     0.8501   0.8565   0.7999
P60     0.8130   0.8384   0.7925
```

Frozen V8-A control:

```text
          2024     2025     2026
P15     0.8566   0.8715   0.8177
P30     0.8418   0.8526   0.7977
P60     0.8068   0.8316   0.7868
```

A2 remains research-only.

## 4. A2 reliability layer

```text
R15 = current P15 percentile vs immediately prior 288 completed M5 P15
R30 = same for P30
R60 = same for P60

EXTREME = all R >=90
HIGH    = all R >=75
QUIET   = all R <=25
NORMAL  = otherwise
```

The current value must not enter its own rank population.

For factual V8 events, HIGH and EXTREME beat the same-calendar-month movement base rate in all 32 evaluated months from 2024-01 through 2026-08 at all three horizons under the documented sample rule.

Interpretation hierarchy: relative rank/state first, raw A2 probability second, frozen V8-A remains control, and none determines direction.

## 5. TradingView and probability-candle research

For chart timeframe >M5, P15 probability candles may aggregate completed underlying M5 P15 values:

```text
Open  = first
High  = max
Low   = min
Close = last
```

Do not use the partial current M5. Probability-candle direction is probability direction, not GOLD direction.

Some TradingView GOLD feeds have no usable volume. FULL A2 has seven tick-volume-dependent features. Do not impute missing values into FULL A2.

A separate 79-feature price-only model, `A2-TV79`, was retrained from scratch.

```text
          2024     2025     2026
P15     0.8624   0.8727   0.8161
P30     0.8465   0.8527   0.7961
P60     0.8085   0.8337   0.7832
```

TV79 is TradingView research/shadow only and does not eliminate OHLC/feed differences versus XM GOLD#.

## 6. Session/time interpretation

XM GOLD# project timestamps are interpreted as Cyprus/server time with DST (`Europe/Nicosia`) unless execution evidence proves otherwise.

Strongest recurring movement cluster: `New York local 08:00-10:30`, roughly KST 21:00-23:30 during US DST and 22:00-00:30 during US standard time.

Session is a prior/context variable, not an independent hard edge. NY adds more information at low/mid R; once state is EXTREME, NY vs non-NY adds little incremental immediate-movement information. Do not add session as a hard V8-C LONG filter.

## 7. V8-B negative-result authority

Do not revive equivalent broad standalone direction mining without materially new causal information. Negative authority includes invalid B1 look-ahead, endpoint sign, slope, excursion dominance, micro barriers, V8-A magnitude weighting, selective tails and WAIT/recenter rescue.

Best weak local learned target remained approximately `0.603 / 0.556 / 0.535` AUC. No V8-B deployment authority.

## 8. Frozen V8-C LONG

```text
M5 SMA20 contact-start
current V8-A P15 > prior-288 Q75
raw Stochastic K14 > D3
completed M15 3-bar up
completed H1 3-bar down
=> LONG next M5 open / first real tick
SL = fill -10
TP = fill +10
one position
```

Accepted R0.4:

```text
2024 N152 WR59.87% +29.26R
2025 N165 WR61.21% +37.35R
2026 N139 WR58.99% +25.24R
pooled N456 WR60.09% +91.85R
expectancy +0.201R/trade
PF ~1.49
```

Do not add new LONG entry filters. Current +/-10 full exit validates entry edge only.

## 9. V8-C-S1 SHORT

Research-only / M1 proxy:

```text
2024 N41 WR58.54%
2025 N51 WR54.90%
2026 N48 WR62.50%
pooled N140 WR58.57% +24R
```

No MT5 authority.

## 10. Fresh-P15-75 auto-direction track

Separate from V8-C LONG:

```text
previous completed M5 P15 <75%
current completed M5 P15 >=75%
=> mandatory LONG or SHORT
=> next M5 open
```

Do not replace this with entry on every M5 while P15 remains >=75; that broader population weakened materially.

A broad tournament tested roughly 790 causal M5/M15/H1/H4/M1 technical/activity features, including candle geometry, partial HTF candles, RSI/BB and MACD/BB composites, many oscillators, trend/volatility families, MFI/CMF/OBV/PVT, signed activity, sweep/break/FVG proxies and signed path features.

No robust ~70% all-trigger direction rule emerged. Best compact consumed-development rules were around 59%.

Important: `2026 is already consumed for fresh75 direction research.` Do not call it untouched validation for later fresh75 tick research. GOLD# 2021 remains locked.

If fresh75 research resumes, change information source before adding arbitrary indicator thresholds: raw quote microstructure, CME GC centralized order flow, or macro surprise/context.

## 11. Current primary research: V8-C exit / winner continuation

Do not improve V8-C LONG entry win rate further. First perform a path audit on the exact accepted R0.4 LONG population.

For all 456 trades, reconstruct causal paths and record entry-to-exit MFE/MAE, first +0.5R/+1R, and for +1R winners post-1R continuation to +1.25/+1.5/+2/+3R, post-1R retracement, continuation timing and right-censoring.

Holding-time compression (`~279m -> ~56m -> ~15m`) does not prove spike/reversal because the target remained a fixed $10 while GOLD volatility/price changed.

Exit sequence:

```text
2024 exit discovery
freeze simple exit family
2025 validation 1
2026 validation 2
2021 locked
```

Initial controls: 100% at +1R; partial +1R with +1.5R or +2R runner; partial +1R then BE; simple fixed trailing after +1R. Conditional V8-A/A2/session exits come later only if simple continuation survives.

Success target:

```text
realized WR >=50%
average winner meaningfully >1R
positive cost-adjusted expectancy
no single-year or tiny-sample dependence
```

## 12. Permanent rules

Completed HTF bars are available only when `bar_start + timeframe_duration <= decision_time`. Partial HTF inputs may use only already-observed lower-timeframe data. Right-censored outcomes must not be forced into wins/losses.

Keep movement model, direction, entry, winner continuation, exit, execution, market suitability and portfolio/exposure separate. Do not automatically reuse a variable found in one stage as a filter in another.

## 13. Work order

1. Preserve V8-A and V8-C LONG exactly.
2. Start V8-C LONG path/MFE/MAE/post-1R continuation audit.
3. Freeze exit methodology before opening later validation years.
4. Keep V8-C-S1 separate.
5. Fresh75 new-information-source work is secondary and 2026 is consumed.
6. Keep A2/TV79/TradingView layers research-only until parity/prospective evidence warrants more.
7. Keep GOLD# 2021 locked.

## 14. Reading authority

1. `HANDOFF_V8.md`
2. `V8_C_EXIT_PATH_RESEARCH_PLAN_20260901.md`
3. `V8_FRESH75_AUTODIRECTION_RESEARCH_20260901.md`
4. `V8_A2_TRADINGVIEW_SESSION_VISUALIZATION_20260901.md`
5. `V8_A2_FINAL_RELIABILITY_LAYER_20260901.md`
6. `V8_C_ENTRY_ARCHITECTURE_MT5_VALIDATION_20260901.md`
7. `DECISIONS_V8_RESEARCH_DIRECTION_ADDENDUM_20260901.md`
8. `RESEARCH_STATE_V8.md`
9. `BACKLOG_V8.md`

Always refresh GitHub HEAD before continuing.
