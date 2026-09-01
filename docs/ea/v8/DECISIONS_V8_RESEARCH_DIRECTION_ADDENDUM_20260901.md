# V8 Decisions Addendum — Reliability, Fresh75 and Exit Direction — 2026-09-01

This file continues `DECISIONS_V8_A2_ADDENDUM_20260901.md` from D-V8-077 onward.

## D-V8-077 — Retain A2 percentile rank/state as the primary A2 reliability interpretation
Retain prior-288 R15/R30/R60 and EXTREME/HIGH/QUIET states as the primary A2 interpretation. Absolute probability is secondary and regime-dependent. This does not promote A2 over frozen V8-A.

## D-V8-078 — Treat TV79 as separate, never imputed FULL A2
Do not fill missing TradingView volume into FULL A2. `A2-TV79` is a separately retrained 79-feature price-only survival model and remains research/shadow only.

## D-V8-079 — Probability candles are visualization-only
M15+ P15 candles use completed underlying M5 P15 values: O first, H max, L min, C last. No partial current M5. Probability-candle direction is not GOLD direction.

## D-V8-080 — Use session as prior/context, not a hard V8-C filter
Record NY local 08:00-10:30 as the strongest recurring movement window, but do not add NY-only filtering to frozen V8-C LONG. Session overlaps materially with A2 state, especially EXTREME.

## D-V8-081 — Define fresh-P15-75 cross as a separate auto-direction trigger
Retain previous P15<75 and current P15>=75, mandatory direction, next-M5-open. Do not enter on every bar while P15 stays high.

## D-V8-082 — Record broad fresh75 technical tournament as negative evidence against an obvious ~70% solution
Roughly 790 causal technical/MTF/candle/activity features, including creative oscillator-band composites, did not produce a robust ~70% mandatory-direction rule. Best compact development results remained around 59%. This does not prove direction impossible with new information.

## D-V8-083 — Mark 2026 consumed for fresh75 direction research
2026 was repeatedly inspected during the broad tournament. Do not describe it as untouched validation for later fresh75 tick research. Any earlier wording to that effect is superseded. 2021 remains locked.

## D-V8-084 — Change fresh75 follow-up from indicator proliferation to new information sources
If resumed, prioritize raw XM quote microstructure, CME Gold futures centralized order flow, and macro-event surprise/context before arbitrary new technical thresholds.

## D-V8-085 — Make V8-C LONG exit/path audit the primary research direction
The next primary task is winner continuation and final exit architecture for the exact frozen V8-C LONG entry population. Entry already has ~60% real-tick evidence; payoff expansion is still untested.

## D-V8-086 — Do not infer spike-and-reversal from holding-time compression
The 2024~2026 median holding compression does not prove post-TP reversal because the barrier remained a fixed $10 while price/volatility changed. Measure continuation directly.

## D-V8-087 — Audit all 456 LONG trades, not winners only
Reconstruct all accepted R0.4 paths. For +1R winners additionally record +1.25/+1.5/+2/+3R reach, post-1R retracement, time and right-censoring. Winner-only MFE is insufficient.

## D-V8-088 — Separate exit discovery and validation
Use 2024 for exit discovery, then freeze the candidate family before opening 2025 validation and subsequently 2026 validation. Keep 2021 locked.

## D-V8-089 — Start with simple mechanical exit controls
First compare +1R control, partial +1R with +1.5R/+2R runner, partial +1R then BE, and one simple fixed trailing rule. Do not start with indicator-conditioned exits.

## D-V8-090 — Exit promotion requires WR>=50%, winner>1R and positive full-cost expectancy
Also require validation stability, drawdown/loss-streak reporting and no dependence on a few outsized winners.

## D-V8-091 — Keep V8-C entry and exit research separate
No new LONG entry filter may be introduced to rescue an exit variant. R0.4 entry remains the control.

## D-V8-092 — Keep GOLD# 2021 locked through exit discovery
Do not spend 2021 on fresh75 rescue, session filtering or initial exit design. Use it only after a complete architecture is frozen and merits final temporal validation.

## D-V8-093 — Open V8-A-N as a separate ATR-normalized movement challenger

Decision:

Retain frozen V8-A and V8-A2 unchanged and open `V8-A-N` as a separate research branch.

V8-A-N target scale is:

```text
pre-decision causal M5 Wilder ATR14
barrier = k * ATR
```

Reason:

The same fixed $10 target changed effective difficulty by orders of magnitude across 2022-2026, while ATR-multiple movement base rates were highly stable.

---

## D-V8-094 — Treat fixed-$10 base-rate drift as target-definition evidence, not merely calibration noise

Decision:

The large year-to-year fixed-$10 prevalence shift is not to be treated only as a calibration defect.

Reason:

The normalized excursion distribution itself is stable in ATR units. A fixed dollar barrier represents different volatility-relative distances in different years.

This does not invalidate frozen V8-A; it defines what V8-A measures: absolute-dollar movement under a changing market scale.

---

## D-V8-095 — Retain normalized future excursion as the core V8-A-N research quantity

Decision:

Retain:

```text
Z_H = maximum absolute future excursion over horizon H / causal pre-decision ATR
```

as the portable movement-distance research quantity.

Reason:

Its 15m/30m/60m distribution was highly stable across 2022-2026.

---

## D-V8-096 — Do not deploy independently trained distance probabilities as the final V8-A-N surface

Decision:

Current 0.75-3.00ATR independent survival models are research prototypes only.

A final model must enforce:

```text
farther distance => probability non-increasing
longer horizon => probability non-decreasing
```

Reason:

Rare but non-zero distance-order violations were observed.

---

## D-V8-097 — Retain normalized fresh-75 as the next movement-trigger research family

Decision:

Open the next trigger family:

```text
previous P15(k ATR) <75%
current P15(k ATR) >=75%
```

with initial structural candidates:

```text
k = 1.25 / 1.50 / 2.00 ATR
```

Reason:

All three produced high and materially stable realized movement rates across 2024-2026.

---

## D-V8-098 — N1 trigger selection must be direction-outcome blind

Decision:

Freeze the normalized fresh-high trigger before using LONG/SHORT labels or P/L.

Use:

- movement realization;
- sample count;
- year/month stability;
- spacing/clustering;
- ATR distribution;
- session distribution;
- implementation properties.

Reason:

Selecting k from directional backtest performance would contaminate the trigger with the downstream task and recreate post-hoc selection bias.

---

## D-V8-099 — Old fixed-$10 direction engine does not automatically transfer to normalized fresh-high

Decision:

After N1 freeze, rebuild or revalidate direction on the exact normalized population.

Reason:

The event population changes materially when the target scale changes. A variable useful for fixed-$10 fresh75 cannot be assumed to have the same relation in the normalized population.

---

## D-V8-100 — Retain fixed-$10 $10/$13 as a development comparison control

Decision:

For the consumed fixed-$10 fresh75 branch, retain:

```text
SL $10
TP $13
nominal payoff ~1.30R
```

as the central comparison candidate.

Observed development evidence:

```text
2025 WR52.63% EV +0.207R
2026 WR52.07% EV +0.198R
```

Reason:

It lies inside a broad 1.20-1.35R positive plateau and leaves more WR margin than the 1.35R boundary.

No promotion authority and no further decimal TP optimization.

---

## D-V8-101 — ATR-consistent exit research begins only after normalized direction freeze

Decision:

Do not evaluate the final normalized strategy by simply attaching ATR stops to the old fixed-$10 trigger.

Research order is:

```text
N1 normalized trigger freeze
N2 normalized-population direction freeze
N3 ATR-consistent SL/TP
N4 complete strategy comparison
```

Reason:

Changing only the exit scale while retaining a fixed-$10 movement trigger mixes incompatible target semantics.

---

## D-V8-102 — Shift current primary work to the complete normalized fresh-high architecture

Decision:

The current primary V8 research task is now:

`V8-A-N normalized fresh-high trigger -> direction engine -> ATR-consistent risk/payoff`.

V8-C LONG exit work remains retained as a separate research track but is not the immediate priority.

Reason:

The normalized study uncovered a structural target-scale issue and a high-precision, high-count movement trigger family that warrants direct strategy research.

---

## D-V8-103 — Keep GOLD# 2021 locked through normalized architecture development

Decision:

Do not use 2021 to choose normalized k, direction features or ATR SL/TP.

Reason:

The complete normalized strategy is not frozen. Reserve use is justified only after trigger, direction, risk/payoff and execution semantics are all fixed.
