# V8 Decisions

## D-V8-001 — Open V8 and pause V7 as active research

Date: `2026-08-30`

Decision:

- V8 becomes the active strategy-research generation.
- V7 is paused/preserved as semantic and research history.
- No V7 result is rewritten.
- No V8 production authority exists.

Reason:

The next bottleneck is not another V7 threshold or archetype rule. It is how ambiguous chart context is
represented for machine decision making.

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

These terms can be meaningful to a human while lacking a unique causal numerical definition. Creating
threshold definitions would risk substituting a proxy for the phenomenon being studied.

They may remain human explanatory vocabulary.

---

## D-V8-003 — Separate observable events from contextual meaning

Date: `2026-08-30`

Decision:

Objectively observable events may be encoded explicitly.

Examples include Double-B, MA interaction, Bollinger interaction, session-boundary interaction, causal S/R
interaction and displacement events.

The event does not automatically determine direction or archetype.

Reason:

A common event can be actionable in many different ways depending on the surrounding chart. The anchor and
its meaning must remain separate.

---

## D-V8-004 — Use hybrid visual + numerical representation

Date: `2026-08-30`

Decision:

V8 will treat multi-timeframe rendered chart geometry as a first-class input and retain an exact numerical
sequence in parallel.

Reason:

Rendering does not create new market information, but it preserves spatial/temporal relationships and gives
the model a different inductive bias. Numerical input remains necessary for exact risk, spread and execution.

---

## D-V8-005 — Learn latent context rather than force semantic state labels

Date: `2026-08-30`

Decision:

The model may learn an unlabeled latent representation `z_t`.

We do not require each latent region to be named.

Reason:

The economic decision can be tested directly without proving that a particular human label is the uniquely
correct description of the market.

---

## D-V8-006 — Action-conditioned path is preferred over generic next-return prediction

Date: `2026-08-30`

Decision:

V8 will eventually estimate the consequence of WAIT/ENTER/HOLD/ADD/REDUCE/EXIT under the current context.

Generic 15m up/down prediction may remain a diagnostic baseline but is not the central V8 formulation.

Reason:

The user's target behavior is sequential campaign management, including re-entry/add-on and partial profit
taking as the chart evolves.

---

## D-V8-007 — Overlapping decisions belong to one campaign

Date: `2026-08-30`

Decision:

Multiple actions in one underlying move must be grouped under one campaign with explicit total risk and
exposure.

Reason:

Previous research found that counting overlapping high-confidence signals as separate trades can manufacture
a false edge.

---

## D-V8-008 — GOLD 2022-2026 are open development; GOLD 2021 remains reserve

Date: `2026-08-30`

Decision:

- GOLD# 2022-2026: open/consumed V8 development evidence.
- GOLD# 2021: untouched final temporal reserve.

Reason:

Prior project work has already inspected 2022-2026 in various forms. V8 must not relabel them pristine simply
because the new representation is different.

---

## D-V8-009 — Representation correctness precedes profitability

Date: `2026-08-30`

Decision:

The first V8 deliverable is the causal chart/numerical representation and audit harness.

No new strategy will be promoted from P/L before future-leakage, timestamp parity, event timing and campaign
state are verified.

---

## D-V8-010 — V8 does not assume images are intrinsically superior

Date: `2026-08-30`

Decision:

Visual, numerical and fused representations must be compared using the same causal information.

Reason:

The hypothesis is about representation and inductive bias, not about adding information that does not exist
in the underlying market data.
