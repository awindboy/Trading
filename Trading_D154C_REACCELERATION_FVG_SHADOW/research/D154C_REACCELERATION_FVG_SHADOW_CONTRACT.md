# D-154C Reacceleration-FVG Shadow Contract

Date: 2026-08-22  
Status: **LOCAL SHADOW RESEARCH / NOT STRATEGY AUTHORITY**  
Base Git HEAD: `af4643738192b68109adc5ddc192234619690a20`  
Base EA blob: `42b0632df8388dc8800c6b4b6820272c6cff1208`

## Causal question

D-154B showed that waiting for same-direction M1 owner completion and then chasing the confirmation price is not robust.

D-154C asks:

> After the first same-direction post-Fill M1 INITIAL_BOS, does the market create a new same-direction FVG and later retrace into it **before the original trade's +1R/SL terminal**, allowing a materially better entry price while preserving the original structural stop premise?

## Population

Only actual V2 EXTERNAL_CONTINUATION fills where M1 is `TRANSITION` at actual Fill.

## Sequence

```text
actual baseline Fill while M1 TRANSITION
-> first post-Fill M1 INITIAL_BOS
-> require SAME direction
-> first same-direction M1 FVG with:
     FVG available after confirmation
     FVG candle2/displacement candle starts at or after confirmation
-> freeze this first FVG
-> wait for first executable retest
-> shadow Entry at FVG proximal edge
```

No second FVG retry is allowed.

## Shadow geometry

- LONG Entry = FVG top.
- SHORT Entry = FVG bottom.
- SL = original normalized baseline SL.
- Risk = new FVG-edge Entry to original SL.
- +1R = recomputed from this new risk.
- TP context = original frozen structural objective.
- Structural objective must still provide at least +1R from the new Entry.

## Causal terminal

Before shadow Fill:
- original +1R first -> no delayed Entry;
- original SL first -> no delayed Entry;
- tester end -> right-censored;
- no post-outcome backfill.

After shadow Fill:
- track new +1R vs original SL;
- original baseline +1R does not terminate the shadow;
- HTF map loss is logged as context only.

## Excluded

- INITIAL_BOS immediate market Entry
- post-SL re-entry
- second/third FVG rescue
- new SL model
- EM
- threshold optimization
- market-specific parameter tuning

## Promotion boundary

A promising result still does not authorize a strategy change. It must first show:
- useful retest coverage;
- improved shadow survival;
- no GOLD/BTC or LONG/SHORT relation collapse;
- retained structural objective room;
- exact OFF/ON non-interference parity;
- later validation outside GOLD25/BTC25.
