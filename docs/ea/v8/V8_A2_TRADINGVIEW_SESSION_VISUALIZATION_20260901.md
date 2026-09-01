# V8-A2 TradingView, Probability-Candle and Session Research — 2026-09-01

Status: `RESEARCH / INFORMATION-SURFACE CONSOLIDATION`
Authority: `NO PRODUCTION AUTHORITY`

## A2 reliability ranks
R15/R30/R60 are prior-288 completed-M5 percentile ranks of P15/P30/P60. EXTREME = all>=90, HIGH = all>=75, QUIET = all<=25. They are retained because the fixed-$10 base rate changes strongly by regime.

## Probability-candle contract
M5 retains P15/P30/P60 lines. M15+ may display P15 OHLC candles from completed M5 P15 values belonging to the chart bar: O first, H max, L min, C last. The developing candle updates only when another M5 completes. An up candle means probability increased, not that GOLD is bullish.

## TradingView missing volume
FULL A2 has seven tick-volume-dependent features: tickrate_15/60/240/1440 and tickratio_15_240/60_1440/240_1440. Some TradingView feeds have no usable volume. Inference-time zero/mean imputation was rejected because it degraded ranking.

## A2-TV79
A separate 79-feature model was retrained without those seven features using the same strict survival target.

| H | 2024 | 2025 | 2026 |
|---|---:|---:|---:|
| 15m | 0.86238 | 0.87271 | 0.81614 |
| 30m | 0.84648 | 0.85275 | 0.79608 |
| 60m | 0.80852 | 0.83370 | 0.78322 |

TV79 is a TradingView research fallback, not FULL A2 and not an XM-feed equivalent.

## Session/time
Project GOLD# timestamps are consistent with Cyprus/XM server time with DST (`Europe/Nicosia`). Strongest recurring movement cluster was NY local 08:00-10:30, roughly KST 21:00-23:30 during US DST and 22:00-00:30 during US standard time.

## Session x R
NY raises movement prior strongly at low/mid R. HIGH-but-not-EXTREME benefits from NY context. Once state is EXTREME, NY vs non-NY adds little incremental immediate-movement information. Therefore session is context/prior, while R is current realized movement-state measurement. Do not double-count them as independent edges.

Simple London-AM sweep/reclaim and breakout/acceptance proxies did not show stable enough direction-free movement lift to become hard filters. Directional liquidity remains a separate research question.

## Authority
TV79, probability candles, session display and R/state visualization do not change frozen V8-A or V8-C strategy authority. Compile/application and prospective feed parity must be verified separately.
