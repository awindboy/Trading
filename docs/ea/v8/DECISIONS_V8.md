# V8 Decisions

## D-V8-001 — Open V8 and pause V7 as active research

Date: `2026-08-30`

Decision:

- V8 becomes the active strategy-research generation.
- V7 is paused/preserved as semantic and research history.
- No V7 result is rewritten.
- No V8 production authority exists.

Reason:

The next bottleneck is not another V7 threshold or archetype rule. It is how ambiguous chart context is represented for machine decision making.

---

## D-V8-002 — Do not hard-label ambiguous market states by default

Date: `2026-08-30`

Decision:

The base V8 system will not require hard labels such as:

```text
TREND
RANGE
BREAKOUT
BASIC
TURNING
HEALTHY_PULLBACK
TERMINAL_EXPANSION
```

Reason:

These terms can be meaningful to a human while lacking a unique causal numerical definition. Creating threshold definitions would risk substituting a proxy for the phenomenon being studied.

---

## D-V8-003 — Separate observable events from contextual meaning

Date: `2026-08-30`

Decision:

Objectively observable events may be encoded explicitly, but the event does not automatically determine direction or archetype.

Examples include Double-B, MA interaction, Bollinger interaction, session-boundary interaction, causal S/R interaction and displacement events.

---

## D-V8-004 — Start with hybrid visual + numerical representation

Date: `2026-08-30`

Decision:

The initial V8 representation tournament will compare rendered multi-timeframe chart geometry and exact numerical sequence information.

Reason:

Rendering may preserve spatial/temporal relationships while numerical input preserves exact execution quantities. This was an initial hypothesis, not permanent authority.

---

## D-V8-005 — Learn latent context rather than force semantic state labels

Date: `2026-08-30`

Decision:

The model may learn an unlabeled latent representation `z_t`; each latent region does not need a human market-state name.

---

## D-V8-006 — Prefer path/action questions over generic terminal-return prediction

Date: `2026-08-30`

Decision:

Generic future-up/down classification is a diagnostic baseline, not the final V8 formulation. V8 should eventually reason about path and action consequences.

---

## D-V8-007 — Overlapping decisions belong to one campaign

Date: `2026-08-30`

Decision:

Multiple actions inside one underlying move must be grouped under one campaign with explicit total risk and exposure.

Reason:

Counting overlapping high-confidence signals as independent trades can manufacture a false edge.

---

## D-V8-008 — GOLD 2022-2026 are open development; GOLD 2021 remains reserve

Date: `2026-08-30`

Decision:

- GOLD# 2022-2026: open/consumed V8 development evidence.
- GOLD# 2021: untouched final temporal reserve.

---

## D-V8-009 — Representation correctness precedes profitability

Date: `2026-08-30`

Decision:

No V8 strategy is promoted from P/L before future-leakage, timestamp parity, event timing and representation correctness are verified.

---

## D-V8-010 — V8 does not assume images are intrinsically superior

Date: `2026-08-30`

Decision:

Visual, numerical and fused representations must be compared using the same causal information.

Reason:

The hypothesis concerns representation/inductive bias, not adding information that does not exist in the market data.

---

## D-V8-011 — De-scope visual input from the active base path

Date: `2026-08-31`

Decision:

Visual/raster input is no longer required for the active V8 movement-probability path. Exact causal numerical information is preferred unless a later controlled test demonstrates incremental visual value.

Reason:

Low-resolution visual encoding lost information relative to exact numerical geometry, while larger model architecture did not fix the active bottleneck.

---

## D-V8-012 — Use event-close-centered coordinates for price-level representation

Date: `2026-08-31`

Decision:

When V8 represents chart geometry around a decision/event anchor, all price-level variables share `C0 = event/source candle close` and are transformed as `x - C0`.

Reason:

This removes absolute GOLD price-era translation while preserving relative geometry across timeframes. Magnitude/oscillator variables are not shifted by `C0`.

---

## D-V8-013 — Fix the human-facing movement barrier at +/-10.0 price units

Date: `2026-08-31`

Decision:

The current discretionary-support movement target is whether GOLD reaches either `C0 + 10.0` or `C0 - 10.0` within 15/30/60 elapsed minutes.

Reason:

This directly measures meaningful short-horizon price movement without pretending to know direction. The barrier must not be changed without retraining.

---

## D-V8-014 — Separate movement intensity from direction

Date: `2026-08-31`

Decision:

V8 treats `movement likely` and `which direction` as separate research questions. Strong movement-probability evidence does not authorize LONG/SHORT output.

Reason:

Direction models remained near chance or unstable across extensive diagnostics while movement-intensity models were consistently discriminative.

---

## D-V8-015 — Purge training labels that resolve across evaluation boundaries

Date: `2026-08-31`

Decision:

A training example is not eligible merely because its decision timestamp precedes an evaluation boundary. Its outcome/label resolution must also occur before the boundary.

Reason:

A late-period event whose +/-10p outcome resolves in the evaluation period leaks evaluation prices into the training label.

---

## D-V8-016 — Do not rescue weak direction with preprocessing or architecture mining

Date: `2026-08-31`

Decision:

Robust normalization, fractional differentiation, masked pretraining, overlap weighting, larger neural models, event-family splitting, rolling retraining and meta-labeling are not default rescue paths for V8 direction.

Reason:

They were directly tested and did not produce stable strong future-hidden directional information. A reopened direction branch requires a materially new causal source or formulation.

---

## D-V8-017 — Treat multi-horizon realized range/volatility as the active movement representation

Date: `2026-08-31`

Decision:

The active movement-probability branch prioritizes causal multi-horizon range, realized-variation and activity structure rather than broad generic technical-indicator accumulation.

Reason:

Ablations showed that recent range/volatility/activity carried most of the movement information, while event identity and broad indicator snapshots added little.

---

## D-V8-018 — Promote movement probability to MT5 shadow-development

Date: `2026-08-31`

Decision:

Implement a non-trading MT5 indicator that displays continuous 15m/30m/60m movement probabilities and factual event markers.

Reason:

A portable walk-forward logistic model retains strong event-subset discrimination across 2024-2026 and can be translated to MQL with floating-point parity.

---

## D-V8-019 — Historical probability display must be walk-forward causal

Date: `2026-08-31`

Decision:

Historical MT5 values use the model that existed before that evaluation calendar year:

```text
2024 <- 2022-2023
2025 <- 2022-2024
2026 <- 2022-2025
```

No pre-2024 value is shown by the current model pack.

Reason:

Using one final model across old history would create visually convincing but look-ahead-contaminated historical probabilities.

---

## D-V8-020 — Movement probability is a human filter, not trade authority

Date: `2026-08-31`

Decision:

The active near-term product hypothesis is human-assisted discretionary filtering:

```text
factual event
+ movement probability
        ↓
human chart analysis
        ↓
LONG / SHORT / WAIT / SKIP
```

Reason:

Current evidence supports movement-intensity discrimination but not stable autonomous direction or trade expectancy.

---

## D-V8-021 — Prospective logging is required before a trading threshold

Date: `2026-08-31`

Decision:

Do not promote a hard movement-probability threshold for discretionary trading from retrospective chart review. Log every supported event and the human decision prospectively first.

Reason:

Retrospective selection of attractive/high-score winners would create selection bias and could manufacture an apparent human+AI edge.


---

## D-V8-022 — Freeze V8-A movement probability while V8-B is researched

Date: `2026-08-31`

Decision:

V8-A is frozen at its current 10.0-price-unit, 15m/30m/60m movement-probability contract. V8-B research must not change V8-A features, labels, historical model policy or MT5 semantics in order to improve direction results.

Reason:

Movement probability already has positive open-development evidence and must remain an independent control. Direction research must not contaminate the component that already works.

---

## D-V8-023 — Reopen direction only as same-horizon conditional side probability

Date: `2026-08-31`

Decision:

V8-B estimates `q_H = P(UP first | a +/-10 move occurs within H, causal context)` for the same horizons used by V8-A.

Joint probabilities are:

```text
UP_H   = p_H * q_H
DOWN_H = p_H * (1 - q_H)
NO_H   = 1 - p_H
```

Reason:

The old eventual-first-hit direction target mixed radically different resolution times. The new formulation aligns direction with the near-term movement horizon that V8-A actually predicts.

---

## D-V8-024 — Do not use V8-A probability as a direct V8-B direction feature by default

Date: `2026-08-31`

Decision:

V8-B1 does not feed `p15/p30/p60` into the conditional side model. V8-A probabilities enter only through the final joint-probability multiplication.

Reason:

Direct movement-probability features and continuous gating interactions failed to improve side AUC and often reduced it. Extreme movement states also showed lower, not higher, side predictability.

---

## D-V8-025 — V8-B directional support is event-family specific

Date: `2026-08-31`

Decision:

Current V8-B development support includes M5 SMA20, upper-BB and lower-BB contact-start events. H1 Double-B remains movement-only and has no authorized directional probability.

Reason:

M5 families retained strong conditional-side AUC across 2024-2026, while H1 Double-B remained approximately chance in every tested year and horizon.

---

## D-V8-026 — Use signed causal progression as the V8-B1 representation

Date: `2026-08-31`

Decision:

V8-B1 uses regularized logistic modeling of signed multi-horizon price progression and completed M5/M15/H1 technical state. No hard TREND/RANGE/BREAKOUT label is supplied.

Reason:

The strongest single mechanism was H1 progression, but a broader signed context materially improved it. M5-only context was weak, while M15/H1 context remained informative.

---

## D-V8-027 — Require all-event and non-overlap validation for conditional direction

Date: `2026-08-31`

Decision:

Conditional mover AUC is insufficient by itself. V8-B must also improve joint UP/DOWN/NO-MOVE probability on the full event population and survive outcome-blind non-overlap evaluation.

Reason:

Conditioning evaluation on future movers can create an attractive but operationally misleading result. The joint decomposition and non-overlap tests are required to prove practical information survives.

---

## D-V8-028 — Keep GOLD# 2021 locked after the V8-B discovery result

Date: `2026-08-31`

Decision:

Do not open GOLD# 2021 yet. Freeze exact V8-B equations/coefficients, implement shadow-only output and verify parity before deciding whether V8-B is ready for untouched validation.

Reason:

2024-2026 are already consumed development evidence, and the V8-B formulation changed materially during this research cycle.


---

## D-V8-029 — Invalidate V8-B1 due higher-timeframe lookahead

Date: `2026-08-31`

Decision:

The positive V8-B1 conditional-direction result committed at `0529c204...` is classified `INVALIDATED_BY_HTF_LOOKAHEAD` and may not be used as direction evidence or deployment authority.

Reason:

The M15/H1 feature builder selected resampled bars by start timestamp. For decisions inside a bar, this supplied the final completed OHLC/indicator values containing future observations after the decision.

---

## D-V8-030 — Availability time, not bar-start time, governs HTF causality

Date: `2026-08-31`

Decision:

A completed resampled bar is observable only when:

```text
bar_start + timeframe_duration <= decision_time
```

A current partial HTF bar is allowed only if reconstructed from lower-timeframe observations already available before the decision.

Reason:

Bar labels identify intervals; they do not prove that the interval has finished.

---

## D-V8-031 — Preserve V8-A despite V8-B1 invalidation

Date: `2026-08-31`

Decision:

V8-A movement probability remains frozen and valid as open-development evidence.

Reason:

The portable V8-A model uses backward M1-derived range/volatility features and does not depend on the leaky M15/H1 B1 feature path. Its Python-to-MQL equation parity is separate evidence.

---

## D-V8-032 — Block V8-B1 model deployment

Date: `2026-08-31`

Decision:

`config/v8_b1_direction_models.json` is historical invalidated evidence only. No MT5 direction indicator/EA may use those coefficients.

Reason:

The coefficients were fit to a contaminated representation. Correcting input alignment collapses the reported direction skill.

---

## D-V8-033 — Open V8-B2 only as source-of-move causal direction research

Date: `2026-08-31`

Decision:

The next direction branch is `V8-B2 SOURCE-OF-MOVE / CROSS-MARKET CAUSAL DIRECTION`.

Initial external sources are limited to mechanism-linked existing development data:

- USDJPY# primary context;
- XAUEUR# primary cross-gold context;
- BTCUSD# negative control.

V8-A remains frozen.

Reason:

Strictly causal endogenous GOLD features do not show stable strong direction information, while financial-market evidence and prior project data support testing whether USD/cross-market source-of-move information contains incremental sign information.

---

## D-V8-034 — Full-population proper score is mandatory for V8-B2

Date: `2026-08-31`

Decision:

Mover-only conditional AUC remains a diagnostic, but V8-B2 promotion requires improvement of the all-event `NO MOVE / DOWN / UP` distribution relative to corrected GOLD-only and V8-A+prior controls.

Reason:

Conditioning evaluation on a future-known mover population can exaggerate practical usefulness even when the conditional classifier itself is causal.
