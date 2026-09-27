# V13 HA knowledge/source register addendum — HA-6 / HA-7

Date: `2026-09-27`
Base register: `V13_HA_KNOWLEDGE_AND_SOURCE_REGISTER_20260926.md`
Status: `SOURCE / LOCAL-EVIDENCE ADDENDUM / NO NEW TRADE AUTHORITY`

## A. Additional platform/reference sources used

### S15 — MetaQuotes iATR reference

- class: `A`
- URL: https://www.mql5.com/en/docs/indicators/iatr
- role: platform reference for ATR handle/period semantics.
- V13 use: HA-6C uses completed-H4 ATR14 as a normalization coordinate only.

### S16 — MetaQuotes iADXWilder reference

- class: `A`
- URL: https://www.mql5.com/en/docs/indicators/iadxwilder
- role: platform reference for Welles Wilder ADX with MAIN, +DI and -DI buffers.
- V13 use: HA-6D1 isolated ADX/DMI before considering any SuperTrend stack.

### S17 — MetaQuotes ADX Wilder CodeBase implementation

- class: `A/B`
- URL: https://www.mql5.com/en/code/8
- role: explicit Wilder-style +DM/-DM, True Range, smoothing and ADX
  construction used to resolve formula semantics in HA-6D1.
- caveat: one MetaTrader help page exposed a conflicting True-Range term; the
  HA-6D1 receipt records the discrepancy for any future Python/MQL5 parity test.

### S18 — MetaQuotes MqlRates history structure

- class: `A`
- URL: https://www.mql5.com/en/docs/constants/structures/mqlrates
- role: platform semantics for separate `tick_volume` and `real_volume` fields.
- V13 use: HA-6E treats GOLD# tick volume as broker-feed activity because real
  volume is zero in the supplied export.

### S19 — Recent MQL5 tick/volume research leads

- class: `B/D`
- URLs:
  - https://www.mql5.com/en/articles/22628
  - https://www.mql5.com/en/articles/17065
- role: implementation/research leads for normalized volume participation.
- caveat: no external threshold or profitability claim was imported. V13 first
  audited broker data semantics and stability.

## B. Local evidence mapping

### HA-6A HASTOC

External source S11 provided the formula research lead. V13 reproduced the
paper sample before GOLD# outcome analysis. HASTOC10 has strong pooled lifecycle
ordering but much of it overlaps HA morphology/H1 state. Retain as a model
feature candidate only.

### HA-6B moving-average context

External source S09 motivated EMA50 broad context and EMA20 high/low boundaries.
V13 split them into separate attribution-preserving probes. Both add some slower
context but produce severe long-Journey false warnings. No alignment rule.

### HA-6C ATR

S15 plus the existing volatility/trend source family support exact semantics.
V13 result: ATR14 is valuable as a cross-era coordinate, not a transition gate.
Raw GOLD price-unit thresholds should be treated as era-dependent unless
normalized.

### HA-6D1 ADX/DMI

S16/S17 support exact indicator semantics. ADX level is independent-looking but
weak/unstable; DMI direction is highly redundant with MA context; ADX falling
loses incremental effect after the full prior-state stack. Branch stopped before
SuperTrend.

### HA-6E tick-volume participation

S18 establishes that tick and real volume are different fields. GOLD# real
volume is zero in the supplied data; tick volume is treated only as quote/tick
activity. Absolute tick counts drift strongly by year/session, so HA-6E uses a
causal same-slot trailing-median normalization. Universal volume separation is
mostly morphology redundancy; persistent-H1-opposition interaction is stronger
but not sufficient for an exit.

### HA-7 first action

The first action was derived only after HA-6E's mechanism survived observation.
It skipped one add-on Child on `persistent_opposition + relative_tick_volume20
> 1.0`. The full-window action worsened net points and right-tail preservation;
it is rejected. This failure is local evidence against deterministic threshold
mining, not evidence that participation information is useless for conditional
state modeling.

## C. Source boundary going into HA-8

HA-8 may use HA-0..HA-6 fields as model features because their semantics and
causal timing are documented. It may not import external ML model rankings,
feature thresholds or reported profitability. Engineering sources such as S13
are relevant only if a model later moves toward ONNX/MT5 deployment.
