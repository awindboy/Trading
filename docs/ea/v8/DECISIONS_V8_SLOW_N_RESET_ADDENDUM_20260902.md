# V8 Decisions Addendum — A-N Semantic Reset / Slow-Scale Research — 2026-09-02

This file continues the V8 decision history after `D-V8-112` in `DECISIONS_V8_RESEARCH_DIRECTION_ADDENDUM_20260901.md`.

## D-V8-113 — Separate M5-volatility-relative excursion from the intended meaningful-move probability

Decision:

The existing V8-A-N formulation:

```text
barrier = k * pre-decision M5 ATR14
```

is retained as valid research for **M5-volatility-relative excursion**, but is superseded as the active interpretation of the user's intended A-N trading question.

Reason:

Because M5 ATR changes every completed M5 bar, the actual predicted target changes every five minutes. The intended use is to normalize broad era/regime differences in meaningful opportunity size, not to continuously resize the practical target from the most recent M5 volatility.

---

## D-V8-114 — Do not erase or relabel the old V8-A-N research as invalid

Decision:

Preserve all old M5-A-N models, ledgers, N1/N2/N3/N4 results and documentation as historical development evidence for the question they actually answered.

Reason:

The causal calculations and statistical findings remain informative. The problem is semantic alignment with the active strategy objective, not fabricated data.

---

## D-V8-115 — Open `V8-A-N-SLOW` as the active replacement research line

Decision:

Use `V8-A-N-SLOW` as a transitional active research name until the slow-scale target is formally frozen.

Intended question:

```text
P(reach a slowly era/regime-normalized meaningful movement distance within H)
```

Direction remains separate.

Reason:

The naming preserves historical traceability while preventing old M5-A-N results from being confused with the replacement architecture.

---

## D-V8-116 — ATR may set broad scale, but must not chase every M5 in the active Slow-N line

Decision:

A Slow-N scale must be derived from fully completed higher-timeframe information and held fixed for a defined block.

No partial current HTF candle may update the scale.

Reason:

This preserves causal regime normalization without turning a short-term lagging-volatility reading into a continuously moving TP/SL question.

---

## D-V8-117 — Retain `0.25 * previous-completed H4 ATR14` as the provisional primary scale candidate

Decision:

Carry forward:

```text
T = 0.25 * Wilder ATR14 from previous completed H4 bar
T held constant for the next H4 block
```

for formalization.

Do **not** yet call it frozen N1 authority.

Development evidence:

```text
median T / 15m base hit
2022  2.33p / 22.07%
2023  2.14p / 21.72%
2024  3.03p / 22.02%
2025  5.07p / 22.75%
2026 10.09p / 20.68%
```

Reason:

H4 currently provides the best semantic balance between M5 over-reactivity and D1 staleness. H1 and D1 remain comparison candidates until formal freeze.

---

## D-V8-118 — Do not choose the slow scale from direction accuracy or trading P/L

Decision:

Slow scale / multiplier selection may use:

- target-size meaning;
- annual/monthly/quarterly movement difficulty;
- update cadence;
- block concentration;
- implementation/causality properties.

Do not choose it because a downstream direction rule or exit earns more.

Reason:

The movement contract must be frozen before direction/economics to avoid target contamination.

---

## D-V8-119 — Retain fixed $10 and legacy M5-A-N as controls, not competitors to be rewritten

Decision:

Keep:

```text
V8-A/A2 fixed +/-10
legacy M5-A-N volatility-relative excursion
```

as separate controls/measurement surfaces.

Reason:

They answer useful distinct questions and provide reference points for absolute versus rapidly normalized versus slowly normalized movement.

---

## D-V8-120 — Treat the first H4 P15 result as a lightweight target-design probe only

Decision:

Do not promote the current H4 coefficients/metrics as the final model.

Probe result:

```text
fresh75 hit
2024 78.55% N648
2025 78.53% N531
2026 76.47% N323
```

The probe used outcome-blind 25-minute training de-overlap for computational efficiency.

Reason:

The result is sufficient to justify formal research, but full model architecture, calibration, quarter stress and reproducible pack are not yet frozen.

---

## D-V8-121 — Reset all old M5-A-N downstream percentages to `REVALIDATION REQUIRED` for Slow-N

Decision:

Do not transfer old numeric results from:

- N2-R1;
- chart voters/MTF states;
- M1 structure/transition;
- raw tick panel/interactions;
- Stoch/tick `0001`;
- Path anti-edge;
- Bollinger states;
- trusted-state hierarchy;
- N3/N4 economics.

Reason:

Changing N1 changes the event population, movement distance and direction first-hit label.

The old results remain valid only on their old population.

---

## D-V8-122 — Preserve old downstream definitions as preregistered transfer hypotheses

Decision:

Before new Slow-N feature discovery, rerun frozen old definitions wherever semantically possible.

Priority:

```text
M5 Stoch D + relative tick 0001
M1 confirmed structure confidence
M1 Stoch alignment / transition
Path relative 1110 anti-edge
BB-A / BB-B / BB-C / BB-D
```

Also rerun prior failed generic panels as negative controls.

Reason:

This turns previous development into useful prior hypotheses instead of retrospectively redesigning rules on the new population.

---

## D-V8-123 — Preserve V4 tick alignment authority, discard V1/V2/V3 tick performance

Decision:

Carry only V4 wall-clock alignment/audit methodology into Slow-N tick work.

Do not reuse V1/V2/V3 tick performance claims.

Reason:

V1-V3 queried ticks at an erroneous Helsinki-shifted clock. V4 demonstrated ~0.98 raw-tick/M1 activity correlation and no after-decision ticks.

---

## D-V8-124 — Keep M1 as an intermediate transition layer, not another generic indicator-majority engine

Decision:

Retain M1 causal structure/transition instrumentation for Slow-N, but do not proliferate M1 RSI/MACD/MA/etc. as independent votes without new evidence.

Reason:

Legacy M1 standalone voters were near 50%, while cross-scale transition interactions were the interesting result.

---

## D-V8-125 — Keep Bollinger(20,2) as state/context representation

Decision:

Retest Bollinger via residence, trigger location, normalized SMA-gap path, band-width path and center crossings.

Do not convert each component into a LONG/SHORT voter.

Reason:

Legacy evidence showed weak marginal components but more informative state paths, with substantial multiple-testing caveats.

---

## D-V8-126 — Old N2-R1 may be a transfer diagnostic but is not a native Slow-N baseline

Decision:

If old N2-R1 is rescored on Slow-N events, label it `legacy-transfer diagnostic`.

Do not silently promote it as the Slow-N control because it includes old M5-A-N probability semantics, including an old P60 vote.

---

## D-V8-127 — Reopen exits only after the new movement population and direction architecture are frozen

Decision:

Do not carry old N3 ATR exits into Slow-N merely because both use ATR language.

After Slow-N direction freeze, preregister a new consistent risk/payoff contract, including whether entry-time H4 scale remains fixed through the full trade.

Reason:

Exit semantics must match the new slowly updated movement contract.

---

## D-V8-128 — The new population does not restore untouched temporal validation

Decision:

Treat 2022-2026 as consumed development evidence even when the Slow-N event population is newly generated.

Reason:

These years have already shaped architecture, hypotheses and scale research. Changing the population does not reset the evidence clock.

`GOLD# 2021` remains locked.

---

## D-V8-129 — The existing MT5 `V8ANP15ContextIndicator` is legacy M5-A-N instrumentation

Decision:

Keep the indicator source as a historical/research artifact, but do not use it as the implementation of the active Slow-N P15.

Reason:

It embeds the `1.50 * pre-decision M5 ATR14` model and therefore answers the superseded M5-relative question.

A new Slow-N MT5 indicator may be built only after the slow model contract is frozen and Python parity is established.
