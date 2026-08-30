# V8 Research State

Status: `ACTIVE / SHADOW IMPLEMENTATION`
Date: `2026-08-31`
Current phase: `V8-005A MOVEMENT PROBABILITY SHADOW INDICATOR`
Production authority: `NONE`
EA authority: `NONE`
Direction authority: `NONE`

## Phase map

### V8-000 — Representation reset
`COMPLETE`

V8 rejected mandatory hard TREND/RANGE/BREAKOUT/TURNING state labels and separated factual anchors from contextual meaning.

### V8-001A — Causal representation foundation
`COMPLETE / PASS`

Completed:

- causal M1/M5/M15/H1 streams;
- completed-bar/no-future boundary;
- deterministic event ledger;
- indicator-prefix invariance checks;
- event/source timestamp parity;
- event-close-centered price-coordinate audit;
- translation-invariance audit.

### V8-001B / V8-002 — Representation and direction diagnostics
`COMPLETE / DIRECTION HYPOTHESIS WEAKENED`

Findings:

- exact numerical geometry retained more information than the first raster branch;
- visual/fused complexity did not create stable direction edge;
- future excursion magnitude was more learnable than sign;
- simple nearest-neighbor chart similarity was not a stable directional predictor.

### V8-003 — 10p direction / preprocessing tournament
`COMPLETE / DIRECTION PATH REDIRECTED`

Target:

```text
which is reached first: C0 + 10.0 or C0 - 10.0
```

Research included:

- OHLC vs indicator-history input;
- multi-lag dynamics;
- robust normalization;
- fractional differentiation;
- overlap/uniqueness weighting;
- purged chronological boundaries;
- self-supervised reconstruction;
- linear / LightGBM / TCN / patch models;
- competing-risk direction+time modeling;
- event-family splits;
- Double-B follow-up chains;
- one-active/non-overlap population;
- rolling/online retraining;
- meta-labeling.

Stable strong direction information was not demonstrated. A representative competing-risk direction sequence degraded from roughly `0.523 -> 0.510 -> 0.475` across 2024/2025/2026.

### V8-004 — Movement-intensity separation
`COMPLETE / POSITIVE DEVELOPMENT EVIDENCE`

The learnable component is near-term movement intensity rather than sign.

Structured multi-horizon M1 range/realized-volatility preprocessing produced strong 10p barrier-crossing discrimination over 15m/30m/60m horizons.

The strongest research benchmark reached approximately:

```text
15m: 2024 0.883 / 2025 0.861 / 2026 0.800
30m: 2024 0.868 / 2025 0.844 / 2026 0.789
60m: 2024 0.838 / 2025 0.831 / 2026 0.784
```

The key explanatory variables were recent realized range/volatility/activity and time context, not event identity or a broad generic technical-indicator snapshot.

### V8-005A — MT5 movement-probability shadow indicator
`IMPLEMENTED / AWAITING USER METAEDITOR COMPILE + RUNTIME PARITY`

Artifact:

`mt5/indicators/V8MovementProbabilityIndicator.mq5`

Portable event-subset AUC:

```text
15m: 2024 0.865 / 2025 0.873 / 2026 0.815
30m: 2024 0.844 / 2025 0.851 / 2026 0.796
60m: 2024 0.807 / 2025 0.829 / 2026 0.781
```

The indicator is non-trading and direction-free.

### V8-005B — Prospective human+AI shadow study
`PENDING`

Log every supported event, all three probabilities, human discretionary direction/skip decision and eventual trade result.

Primary question:

> Does human directional/trade performance improve as movement probability increases?

### V8-006 — GOLD# 2021 reserve
`LOCKED`

Do not open.

## Current model authority

The portable MT5 shadow model is a continuous-M5 walk-forward logistic representation with 53 causal M1 range/volatility features.

Historical models:

```text
2024 <- 2022-2023
2025 <- 2022-2024
2026 <- 2022-2025
```

Target:

```text
P(price reaches current completed-M5 close +/- 10.0 within H)
H in {15m,30m,60m}
```

No LONG/SHORT probability is authorized.

## Current data interpretation

The strongest V8 evidence currently supports:

```text
GOLD past context -> movement intensity / speed: strong
GOLD past context -> future sign: weak / unstable
```

This is a research result, not a philosophical assumption. It emerged after repeated falsification of direction-oriented representations and models.

## Main restrictions

Do not:

- convert movement probability into automatic direction;
- claim it is liquidity probability;
- claim it is trade win-rate probability;
- change the 10.0 barrier without retraining;
- apply the 2026 model historically to 2024/2025;
- open GOLD# 2021 early;
- retrospectively mine a discretionary threshold from selected winning screenshots.

## Current required documents

- `V8_RESEARCH_JOURNEY.md` — complete research reasoning/history;
- `V8_005_MOVEMENT_PROBABILITY_INDICATOR.md` — current MT5 model/implementation contract;
- `DECISIONS_V8.md` — durable decisions;
- `HANDOFF_V8.md` — immediate continuation state.
