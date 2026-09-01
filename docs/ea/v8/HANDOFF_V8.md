# V8 Development Handoff

Last updated: `2026-09-02`
Current phase: `V8-A-N TARGET-SEMANTICS RESET / SLOW-SCALE FORMALIZATION / DOWNSTREAM REVALIDATION PENDING`
Production authority: `NONE`
Market: `GOLD#`
Untouched reserve: `GOLD# 2021`
Package base Git HEAD: `7344f8c3918a89e3fc6d30f1df64d90d567ecda5`

## 1. Read this first

The previous active V8-A-N architecture used a barrier that changed every M5:

```text
barrier = 1.50 * pre-decision M5 Wilder ATR14
N1 = fresh P15 75-cross
```

This is retained as a legitimate **M5-volatility-relative movement detector**, but it answered a different question from the intended trading use.

The intended P15 question is:

> Is a meaningful tradable movement likely in the next 15 minutes, with the meaning/difficulty of “meaningful” adjusted slowly across market eras/regimes rather than every five minutes?

Therefore the old N1 is no longer the active strategy-scale authority. All direction/M1/tick/Bollinger/exit results conditioned on it are historical development findings and must be rerun.

Current chain:

```text
V8-A fixed-10 control
        +
legacy M5-A-N lessons
        ↓
V8-A-N-SLOW target semantics
        ↓
formal slow scale freeze
        ↓
formal P15/P30/P60 rebuild
        ↓
new fresh75 N1 freeze
        ↓
rerun direction / M1 / tick / Bollinger
        ↓
freeze direction
        ↓
reopen economics/execution
```

## 2. Provisional Slow-N target

Current primary candidate:

```text
At each new H4 block:
ATR_H4 = Wilder ATR14 from the previous fully completed H4 bar
T = 0.25 * ATR_H4
hold T constant for the entire next H4 block

P15 = P(reach C0 +/- T within 15m)
```

This is **provisional**, not final N1 authority.

Why H4 currently leads:

```text
0.25*H4 ATR14 target median / 15m hit base rate
2022  2.33p / 22.07%
2023  2.14p / 21.72%
2024  3.03p / 22.02%
2025  5.07p / 22.75%
2026 10.09p / 20.68%
```

Target update rate per M5 transition:

```text
M5 1.50ATR  100.00%
H1 0.50ATR    8.34%
H4 0.25ATR    2.18%
D1 0.10ATR    0.36%
```

Interpretation:
- M5 is too reactive for the intended scale semantics.
- H1 is viable but updates hourly.
- H4 is the current balance candidate.
- D1 is too slow; 2026 quarterly difficulty drifted materially.

Do not tune H4 decimals from trade outcomes.

## 3. First Slow-N P15 probe

Research-only 86-feature survival probe with outcome-blind 25-minute training de-overlap:

```text
H4 0.25ATR

             AUC15    P15>=75 hit      fresh75 hit
2024         .8142       82.73%          78.55% N648
2025         .7650       81.46%          78.53% N531
2026 YTD     .7770       80.58%          76.47% N323
```

Training phase shift produced broadly similar results.

Important caveat: this is not the final official model and not untouched validation. Quarter-level fresh75 precision is less uniform than annual results; 2026Q2 was ~69.75%.

## 4. Legacy M5-A-N downstream research — status reset

Old population:

```text
1.50 * M5 ATR fresh75
resolved direction events = 2149
```

Everything below remains useful as a hypothesis, but **none transfers automatically to Slow-N**.

### Chart voter findings

- semantic deterministic 7-voter panel: ~49.6 / 51.6 / 50.9% -> failed.
- expanded MTF panels: generally ~49-52% -> failed.
- market-question equal panel: ~49.9 / 51.1 / 51.9% -> failed.
- refined asymmetric M15+M30 up / HTF short / location long state: ~58.2 / 60.0 / 62.0%, discovery only.
- large chart-state family showed substantial multiple-testing risk; do not promote small 65-70% chart states.

### Raw tick audit and result

V1/V2/V3 raw-tick probes were invalidated because the ledger wall-clock had been shifted through Europe/Helsinki before MT5 tick lookup.

V4 corrected this:

```text
raw tick count vs M1 tickvol correlation: 0.9816 aligned / 0.9863 placebo
aligned coverage: 99.77%
placebo coverage: 94.23%
after-decision ticks: 0
```

The generic tick-direction panel failed near 50%; tick data should not override N2-R1 generically.

### Strong old-population Stoch/tick hypothesis

Let D = M5 Stochastic K>D direction.

Relative tick state `0001`:

```text
NET  opposite D
MOVE opposite D
CLV  opposite D
RUN  same D
```

Following D:

```text
2024 N71 63.38%
2025 N64 68.75%
2026 N40 62.50%
ALL N175 65.14%
```

Restricted-family permutation audit was strong internally (~0.0044 familywise), but this was still consumed-data development evidence.

### M1 bridge findings

M1 standalone direction voters were near 50%.

Useful interactions:

```text
M1 confirmed structure == N2-R1:
N832, N2 accuracy 59.86%
2024/25/26 = 60.07 / 60.12 / 59.15%

M5 Stoch + tick 0001 + M1 Stoch aligned:
N57, 71.43 / 72.73 / 71.43%
pooled 71.93%
shifted-tick placebo pooled 47.12%

M1 Stoch transition subset:
N40, pooled 75.0% (too small)
```

Working hypothesis: pullback-ending / cross-scale re-synchronization.

### Bollinger(20,2) state findings

Bollinger components were weak alone; state paths were more informative.

```text
BB-A: prior middle residence -> trigger near lower but inside
DOWN pooled 60.26%, N78

BB-B: prior middle residence -> trigger above upper + SMA distance widening
UP pooled 59.33%, N150; best cross-window robustness

BB-C: inside bands + normalized SMA gap shifts down + >=2 center crosses
DOWN pooled 63.38%, N71; n=5-specific

BB-D: middle residence + bandwidth contraction + exactly 1 center cross
UP pooled 61.25%, N160; n=5-specific
```

Family-wise scan did not justify promotion. Retain Bollinger as context/state representation, not voter authority.

## 5. Critical transfer rule

Do not say:

```text
Slow-N Stoch/tick = 65%
Slow-N M1-sync = 72%
Slow-N BB-C = 63%
```

Those numbers belong only to the old M5-A-N population.

Correct language:

> These are predefined mechanisms/states to retest on the new Slow-N N1 population.

## 6. Next session work order

### Step A — formal Slow-N scale audit

- exact completed H1/H4/D1 construction;
- no partial HTF values;
- target constancy across each block;
- target-size/base-rate/update-cadence tables;
- quarter/month stress;
- decide/freeze slow scale without direction/P&L.

Current leading candidate: `0.25 * previous-completed H4 ATR14`.

### Step B — official probability rebuild

- strict 60m purge;
- chronological 2024/2025/2026 walk-forward;
- full training population, not just the lightweight probe, unless de-overlap is explicitly frozen as architecture;
- AUC/Brier/logloss/calibration/deciles;
- P15/P30/P60 monotonicity;
- reproducible model pack.

### Step C — new N1 freeze

Profile `P15>=75` and `fresh75` using movement outcomes only. Include H4-block clustering and actual target distance.

### Step D — downstream rerun

Before exploring new rules, rerun old definitions unchanged where semantically possible:

1. legacy deterministic chart panel;
2. M5 Stochastic;
3. M1 structure/transition;
4. V4 tick windows + placebo;
5. preregistered `Stoch D + relative tick 0001`;
6. M1-Stoch alignment/transition;
7. Path Clearance anti-edge;
8. Bollinger BB-A/B/C/D;
9. trusted-state hierarchy;
10. multiplicity audit.

Rules containing old M5-A-N probability values (e.g. old N2-R1 P60 vote) may be scored only as legacy diagnostics; do not silently treat them as native Slow-N features.

### Step E — only after direction freeze

Reopen exit/risk/payoff and MT5 real-tick execution.

## 7. Reserve / evidence discipline

```text
2022-2026 = consumed development evidence
2021 = untouched reserve
```

The new population does not reset the temporal evidence clock.

Do not use 2021 until the complete Slow-N movement + direction + execution architecture is frozen enough to justify reserve expenditure.

## 8. Files to read next

1. `AGENTS_V8.md`
2. this `HANDOFF_V8.md`
3. `V8_A_N_SEMANTIC_RESET_AND_SLOW_SCALE_RESEARCH_20260902.md`
4. `V8_A_N_LEGACY_DOWNSTREAM_REVALIDATION_MAP_20260902.md`
5. `DECISIONS_V8_SLOW_N_RESET_ADDENDUM_20260902.md`
6. `RESEARCH_STATE_V8.md`
7. `BACKLOG_V8.md`
