# V8 Fresh-P15-75 Auto-Direction Research — 2026-09-01

Status: `RESEARCH / NO PRODUCTION AUTHORITY`
Reserve: `GOLD# 2021 LOCKED`

## Trigger
```text
previous completed M5 P15 <75%
current completed M5 P15 >=75%
=> mandatory LONG or SHORT
=> enter next M5 open
```
No abstention is allowed merely to raise win rate.

Fresh crossing is retained; repeated entry on every M5 while P15 remains >=75 materially diluted direction edge.

## Broad feature tournament
Roughly 790 causal features were tested across M5/M15/H1/H4 and M1 activity:
- candle body/wick/close-location/sequence;
- EMA/HMA/ROC/efficiency/acceleration;
- RSI, Stochastic, StochRSI, CCI, Williams %R, CMO, UO, Fisher, Connors, QQE-like;
- MACD/PPO/AO;
- RSI-on-Bollinger and MACD-histogram-on-Bollinger composites;
- ADX/DMI/Aroon/Vortex;
- Bollinger/Keltner/Donchian/squeeze;
- Ichimoku/Supertrend;
- MFI/CMF/OBV/PVT/raw tick volume;
- signed M1 activity pressure;
- previous-day/rolling-location, sweep/break/FVG proxies;
- current partial causal M15/H1/H4 candles;
- signed path/semivariance features complementary to direction-free V8-A.

No robust all-trigger ~70% direction rule emerged. Best compact exhaustion/rejection-style development rules remained around 59%. Repeatedly useful clues were partial H1 wick rejection, M15 short-horizon displacement/efficiency and signed M1 activity, often in contrarian/exhaustion orientation rather than simple trend continuation.

Complex models could fit very high in-sample accuracy but fell back near chance/mid-50s out of sample, confirming large indicator-space overfit risk.

## Evidence status
2025 is consumed discovery and 2026 is consumed development/diagnostic. 2026 is not untouched validation for later fresh75 tick work. Any older text claiming otherwise is superseded.

## Next if resumed
Change information source before adding arbitrary indicator thresholds:
1. raw XM quote/tick microstructure;
2. CME GC centralized volume/order-flow;
3. macro-event surprise/context.

This branch must not alter frozen V8-C LONG. Primary project research is now V8-C exit/winner continuation.
