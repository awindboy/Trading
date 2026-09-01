# V8 Research Instructions

Status: `ACTIVE / V8-A-N-SLOW ONSET + EXTENSION / DIRECTION BOTTLENECK`
Generation: `V8`
Last synchronized: `2026-09-02`
Production authority: `NONE`
Market: `GOLD#`
Open development evidence: `2022-2026`
Untouched reserve: `GOLD# 2021`
Base Git HEAD for this update: `45925b29fbec7d52509652e5787654624ecc0848`

## 1. Read this first

The active A-N interpretation is no longer the legacy per-M5 normalized target.

Legacy branch:

```text
V8-A-N-M5
barrier = k * pre-decision M5 Wilder ATR14
```

It remains valid historical research for **M5-volatility-relative excursion**, but it changes target distance every completed M5 and therefore does not match the intended practical question.

Active replacement branch:

```text
V8-A-N-SLOW

At each M5 decision:
    identify the H4 block containing the DECISION timestamp
    use Wilder ATR14 from the immediately previous fully completed H4 bar
    T = 0.25 * H4 ATR14
    keep T constant throughout that H4 decision block

P15 = P(reach C0 +/- T within 15m)
```

`0.25 * H4 ATR14` is still a **provisional primary scale candidate**, not final production or final N1 authority.

## 2. Current Slow-N probability evidence

The lightweight Phase-0 86-feature survival probe was rebuilt with corrected horizon eligibility and reproduced the prior result closely.

```text
Phase-0
             AUC15     P15>=75 hit       fresh75 hit
2024         .81394      82.61%            78.10%  N653
2025         .76483      81.21%            78.50%  N535
2026 YTD     .77681      80.43%            76.01%  N321
```

A second outcome-blind 25-minute training phase was used as a robustness realization:

```text
Phase-2
             AUC15     P15>=75 hit       fresh75 hit
2024         .81507      83.30%            80.22%  N733
2025         .76485      80.87%            76.34%  N579
2026 YTD     .77583      81.14%            78.08%  N292
```

The two fresh75 event sets overlap only partially:

```text
Phase-0 N1509
Phase-2 N1604
intersection N1133
union N1980
Jaccard = 57.22%
```

Therefore downstream direction candidates must not be accepted from a single probability-model realization alone.


## 3. Higher-horizon extension layer

The 0.25/P15 Slow-N population is now interpreted as an **ONSET** movement detector, not the final movement-distance target.

Movement-only screening of:

```text
H = 60 / 120 / 240m
k = 0.50 / 0.75 / 1.00 H4 ATR
```

found stable annual base rates across 2022-2026.

Retained extension research surface:

```text
V8-A-N-SLOW-EXT
T_ext = 0.75 * previous-completed H4 ATR14

P60  = P(reach +/-T_ext within 60m)
P120 = P(reach +/-T_ext within 120m)
P240 = P(reach +/-T_ext within 240m)
```

2026 median `T_ext` is approximately `30.28p`.

Joint Phase-0 / Phase-2 survival AUC:

```text
P60:
2024 ~.814-.815
2025 ~.769-.770
2026 ~.776-.777

P120:
2024 ~.759
2025 ~.702-.703
2026 ~.716-.718

P240:
2024 ~.730
2025 ~.665-.666
2026 ~.661-.662
```

The current onset fresh75 population itself already has strong larger-move realization:

```text
                2024    2025    2026
0.50ATR / 60m   71.36   71.59   68.22%
0.75ATR /120m   62.63   58.69   56.07%
1.00ATR /240m   54.82   51.21   48.91%
```

Therefore:

```text
0.25/P15 fresh75 = ONSET
0.75 P60/P120/P240 = EXTENSION magnitude/horizon context
```

`P120` is the central extension research coordinate. EXT probability is **not** an entry veto and no EXT fresh trigger is frozen.

Direct higher-horizon P_UP/P_DOWN and signed M1/M5 path direction models failed to transfer. Do not claim that longer horizon solves mandatory direction.

## 4. Downstream revalidation result

### Failed / do not extend

The following old definitions were rerun on Slow-N and did not produce a stable useful direction edge:

- legacy deterministic 7-voter panel;
- M5 Stochastic as standalone direction;
- market-question equal panel;
- immediate pressure;
- oscillator transition;
- M15/H1/H4 structure standalone;
- HTF regime;
- volatility transition;
- location/liquidity;
- M1 tape proxy;
- M1 recent direction;
- M1 pressure;
- M1 Stoch standalone;
- M1 EMA3/8 standalone;
- old asymmetric M15/M30/HTF/location state;
- Bollinger BB-A;
- Bollinger BB-C;
- Bollinger BB-D;
- generic raw-tick majority direction on the available legacy/new overlap.

Do not threshold-rescue or recombine these merely because one year looks positive.

### Positive candidate 1 — Bollinger BB-B

Predefined legacy semantic state:

```text
prior M5 residence mainly around Bollinger middle
+
Slow-N trigger candle closes above upper band
+
absolute normalized distance from SMA20 is moving AWAY

predict UP
```

Phase-0, primary n=5:

```text
2024 N34 58.82%
2025 N17 76.47%
2026 N13 69.23%
ALL  N64 65.63%
```

Phase-2, same definition:

```text
2024 N34 64.71%
2025 N18 66.67%
2026 N11 63.64%
ALL  N63 65.08%
```

The same semantic state stayed above 50% across all year x phase x n={3,5,8} cells tested. This is the strongest current full-Slow-N direction/context candidate.

It remains development evidence and small-sample. Do not promote it as a complete direction engine.

### Positive candidate 2 — Stoch/M1/tick re-synchronization, limited population only

Raw ticks currently exist only for the old M5-A-N event ledger. The new Slow-N event set overlaps that ledger on a limited subset, so this is **not** a full-Slow-N tick test.

On the resolved overlap, predefined relative tick state `0001` versus M5 Stoch direction D:

```text
NET   opposite D
MOVE  opposite D
CLV   opposite D
RUN   same D
predict D
```

Result:

```text
2024 N18 61.11%
2025 N20 70.00%
2026 N7  71.43%
ALL  N45 66.67%
```

The -10m shifted placebo version was 45.0% pooled.

Nested M1 observations:

```text
tick0001 + M1 recent counter-move             N26 65.38%
tick0001 + M1 Stoch aligned with M5 D         N14 85.71%
+ M1 Stoch opposite ~3m earlier, now aligned  N10 90.00%
```

The final two are far too small for authority. They only justify extracting raw ticks for **all new Slow-N N1 decisions**.

## 5. Reproducibility warning

The old M1 confirmed-structure study has a reproducibility gap: the result ledger and definition description remain, but the exact original generation code is not present in the retained package. A fresh reconstruction reached only ~85% parity with the old state labels.

Therefore:

- M1 standalone Stoch/pressure/EMA and other exact-parity components may be transferred normally;
- old M1 confirmed-structure percentages must not be claimed on Slow-N until the exact state generator is recovered or a new definition is explicitly frozen.

## 6. Current authority

```text
Movement onset:
provisional = 0.25 * previous-completed H4 ATR14 / P15 fresh75

Movement extension:
research-only = 0.75 * previous-completed H4 ATR14 / P60-P120-P240
P120 = central research coordinate
no EXT fresh trigger authority

Movement scale:
provisional = 0.25 * previous-completed H4 ATR14, decision-block aligned

Probability model:
Phase-0 86-feature probe = research/shadow visualization only
Phase-2 = robustness model realization only
no final official Slow-N model pack yet

Direction:
NO FROZEN SLOW-N DIRECTION ENGINE

Current leading contexts/hypotheses:
1. BB-B expansion context
2. Stoch -> M1 oscillator transition -> final raw-tick RUN re-synchronization

Economics/exits:
CLOSED until direction architecture improves/freeze
```

## 7. Current work order

1. Preserve ONSET = `0.25 H4 ATR / P15 fresh75`; do not replace it from extension results.
2. Retain `V8-A-N-SLOW-EXT` = `0.75 H4 ATR / P60/P120/P240` as shadow movement context, with P120 central.
3. Extract V4-aligned raw tick windows for the **entire onset fresh75 population**, with -10m placebo.
4. Rerun generic tick negative controls and predefined `Stoch D + relative 0001`.
5. Rerun M1-Stoch alignment/transition on the full tick-covered population.
6. Rebuild Path Clearance natively for the Slow-N target and retest its old-flow anti-edge.
7. Study BB-B interaction with Stoch/M1/tick without arbitrary threshold search.
8. Recover or replace the M1 confirmed-structure generator with explicit parity tests.
9. Do not run more generic higher-horizon direction searches without genuinely new information.
10. Freeze direction before reopening payoff; later preregister EXT-conditioned holding/runner research without dropping onset trades.
11. Keep `GOLD# 2021` locked.

## 8. Indicator authority

`mt5/indicators/V8ANP15ContextIndicator.mq5` remains the legacy per-M5 `1.50*M5 ATR` indicator.

`mt5/indicators/V8SlowNP15ContextIndicator.mq5` is a new **research-only Phase-0 Slow-N probe indicator**. It embeds the Phase-0 scaler/coefficients and is for chart inspection/parity work only.

It must not be described as production authority or final frozen Slow-N probability authority.

## 9. Reading order

1. `HANDOFF_V8.md`
2. `V8_A_N_SLOW_HIGHER_HORIZON_EXTENSION_RESEARCH_20260902.md`
3. `V8_A_N_SLOW_DOWNSTREAM_REVALIDATION_RESULT_20260902.md`
4. `V8_A_N_SEMANTIC_RESET_AND_SLOW_SCALE_RESEARCH_20260902.md`
5. `V8_A_N_LEGACY_DOWNSTREAM_REVALIDATION_MAP_20260902.md`
6. `DECISIONS_V8_SLOW_N_RESET_ADDENDUM_20260902.md`
7. `RESEARCH_STATE_V8.md`
8. `BACKLOG_V8.md`

Always refresh GitHub HEAD before continuing.
