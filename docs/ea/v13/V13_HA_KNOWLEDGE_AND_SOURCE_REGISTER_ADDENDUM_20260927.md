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

## D. X1 external-source lead registered on 2026-09-28

### S20 — ECB EUR/USD daily reference-rate data and release timing

- class: `A` for the ECB data series and its publication semantics; `research
  lead only` for any relationship with GOLD#.
- series: `EXR.D.USD.EUR.SP00.A` (USD for one euro, daily).
- URLs:
  - https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A
  - https://data.ecb.europa.eu/help/api/data
  - https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html
- role: an independently sourced **bilateral, daily** dollar proxy for X1
  observation. It is not a DXY or intraday USD history. The ECB ordinarily
  publishes around 16:00 Central European time on working days; X1 imposes a
  conservative two-broker-calendar-day as-of lag rather than assuming the
  broker clock matches ECB time.
- no trading authority: neither source credibility nor a correlation supplies
  a V13 entry, exit, size, filter, or economic validation.

### S21 — XM MT5 EURUSD# H4 bars and MetaQuotes history API

- class: `A` for MetaQuotes API timestamp/schema semantics; broker-local
  historical market data for the `EURUSD#` values.
- URL: https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesrange_py
- role: X2 same-broker, same-H4-clock bilateral dollar proxy. The MT5 API's
  returned GOLD# H4 series must match the frozen GOLD# CSV bar-for-bar before
  matching EURUSD# H4 closes at the completed gold signal timestamp.
- caveat: this is neither DXY nor centralized FX volume. Available history
  depends on the terminal/broker. No source-derived trade rule or edge claim.

### S22 — broker USDX-DEC26 apparent old history: rejected source lead

- class: `broker-local metadata / do not import as causal historical source`.
- The XM terminal returned 7,197 H4 rows starting in 2022 for a symbol
  described as `US Dollar Index December 2026`, yet the symbol's broker
  `start_time` was 2026-09-10, after the canonical V13 cutoff.
- The old bars may be backfilled synthetic display history. Their historical
  decision-time availability is unproven, so they were **not** used as DXY
  or a trading feature. No edge conclusion can be drawn from this source.

## E. HA-8B ML-method leads reviewed on 2026-09-28

### S23 — MQL5 meta-labeling implementation example

- class: `B`, author article, not platform strategy authority.
- URL: https://www.mql5.com/en/articles/22274
- role: methodological example of leaving a primary signal responsible for
  direction while a secondary model studies participation/sizing quality.
- V13 boundary: HA remains the sole direction/Journey source. The article's
  RSI, triple barriers, 0.55 threshold, bet-size formula, and reported EURUSD
  result are **not** imported. HA-8B only evaluates conditional Child economics.

### S24 — MQL5 discrete-time competing-risk exit example

- class: `B`, author article, not platform strategy authority.
- URL: https://www.mql5.com/en/articles/24106
- role: illustrates time-varying trade-state and survival-risk modeling, and
  explicitly reports that predictive fit need not improve trading outcomes.
- V13 boundary: its fixed TP/SL, R normalization and early-exit policy are
  incompatible with Baseline 0 and were not imported into HA-8B. Its state-
  evolves-over-time lesson motivates auditing Child age and current position
  state, not a new exit rule.

### S25 — MQL5 ONNX platform reference

- class: `A` for terminal model-inference API, not evidence of trading edge.
- URL: https://www.mql5.com/en/docs/onnx
- role: possible later transport after a V13 model, action contract, and
  Python/MQL5 input/preprocessing/output parity pass. No ONNX or EA change is
  part of HA-8B.
