# D-154K — Cross-Scale Reaction / Noise Audit

Status: RESEARCH / SHADOW-ONLY  
Date: 2026-08-23  
Contrast: GOLD25 vs CADJPY25  
Strategy authority: NONE

## Question

When HTF state and protected-to-external geometry look comparable, does the M1 Root reaction / execution geometry operate at a different scale relative to 1R and transaction friction?

## Population and causal windows

Unit: actual execution Fill.

Primary local reaction window:

```text
actual Root-contact M1 bar
->
accepted CHOCH M1 bar
```

Secondary execution window:

```text
accepted CHOCH
->
latest fully closed M1 bar before Fill
```

The audit runs at Fill but reads only bars already completed before Fill.

## Measurements

Raw:
- reaction M1 mean true range and mean high-low range;
- close-path length;
- directional net displacement and efficiency;
- total high-low range;
- favorable/adverse excursion;
- CHOCH->Fill pullback.

Cross-scale:
- actual 1R / reaction TR;
- selected FVG width / reaction TR;
- Root width / reaction TR;
- current frozen-plan HTF span / reaction TR;
- HTF remaining distance / reaction TR;
- spread / reaction TR and spread / 1R;
- signed fill slippage / reaction TR and / 1R;
- CHOCH->Fill pullback / reaction TR and / 1R.

Price-relative and tick-normalized risk/noise/spread are also logged.

Spread is a `SymbolInfoTick` snapshot at the Fill callback and is not claimed to be an exact historical bid/ask reconstruction of the broker fill tick.

## Prohibited inference

No threshold, score, symbol-specific gate, LONG/SHORT exception, Entry/SL/TP/sizing/SP/EM change is allowed in this phase.
