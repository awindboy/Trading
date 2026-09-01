# V8 Research Instructions

Status: `ACTIVE / V8-A-N TARGET-SEMANTICS RESET / SLOW-SCALE FORMALIZATION`
Generation: `V8`
Last synchronized: `2026-09-02`
Production authority: `NONE`
Market: `GOLD#`
Open development evidence: `2022-2026`
Untouched reserve: `GOLD# 2021`
Base Git HEAD for this documentation update: `7344f8c3918a89e3fc6d30f1df64d90d567ecda5`

## 1. Read-this-first correction

The earlier active V8-A-N line used:

```text
scale = causal pre-decision M5 Wilder ATR14
barrier = 1.50 * M5 ATR14
fresh trigger = previous P15 <75%, current P15 >=75%
```

That research is mathematically valid for the question:

> will GOLD travel an unusually large distance relative to its **current M5 volatility**?

However, it does **not** match the intended trading question that motivated A-N:

> will GOLD soon make a **meaningful tradable move**, while ATR is used only to keep the meaning/difficulty of that move comparable across changing market eras/regimes?

Because M5 ATR changes every completed M5 bar, the old formulation changes the predicted barrier every five minutes. For the active strategy line this is now treated as a **target-semantics mismatch**, not as bad data or a coding failure.

## 2. Current branch map

```text
V8-A
FROZEN / ABSOLUTE-$10 MOVEMENT CONTROL
P(reach C0 +/-10 within 15/30/60m)

V8-A2
RETAINED ABSOLUTE-$10 86-FEATURE SURVIVAL CHALLENGER / NOT PROMOTED

V8-A-N-M5 (historical name: V8-A-N)
RETAINED LEGACY M5-VOLATILITY-RELATIVE RESEARCH BRANCH
barrier = k * pre-decision M5 ATR14
valid for its own question, but SUPERSEDED as the active strategy-scale interpretation

V8-A-N-SLOW
ACTIVE REPLACEMENT RESEARCH LINE FOR THE INTENDED A-N SEMANTICS
provisional primary scale candidate = 0.25 * previous-completed H4 ATR14
scale frozen for the next H4 block
NOT YET FROZEN AS FINAL N1

LEGACY M5-A-N N1/N2/N3/N4
HISTORICAL DEVELOPMENT EVIDENCE ONLY
all downstream numbers are conditional on the old 1.50*M5-ATR fresh75 population
must be rerun on the new Slow-N population before reuse

V8-C LONG / V8-C-S1
SEPARATE retained branches; no change from this reset
```

The `V8-A-N-SLOW` name is transitional so history is not rewritten. If the slow-scale architecture is finally frozen, documentation may consolidate the active name back to V8-A-N while retaining M5-A-N as historical provenance.

## 3. Intended probability contract

P15 must answer a stable economic question:

```text
Given a slowly updated, era/regime-normalized meaningful-move distance T,
what is P(reach C0 + T OR C0 - T within 15 minutes)?
```

Direction is separate.

ATR is permitted to normalize the **meaningful movement scale across regimes**, but it must not make the target chase every M5 fluctuation.

Current provisional candidate:

```text
At the start of each H4 block:
    scale = Wilder ATR14 from the previous fully completed H4 bar
    T = 0.25 * scale
    hold T constant for the whole next H4 block

P15 = P(reach +/-T within 15m)
P30 = P(reach +/-T within 30m)
P60 = P(reach +/-T within 60m)
```

No partial/in-progress H4 candle may enter the scale.

## 4. Why H4 is the current primary candidate

Development probe, not final authority:

### Target median / realized 15m base rate

```text
0.25 * H4 ATR14

2022 median T  2.33p / hit15 22.07%
2023 median T  2.14p / hit15 21.72%
2024 median T  3.03p / hit15 22.02%
2025 median T  5.07p / hit15 22.75%
2026 median T 10.09p / hit15 20.68%
```

This is close to the intended behavior: roughly 10p is a meaningful move in the current high-volatility regime, while earlier low-volatility eras receive a smaller but similarly difficult target.

### Update cadence

```text
M5 1.50ATR: target changes on ~100% of M5 transitions
H1 0.50ATR: ~8.34%
H4 0.25ATR: ~2.18%
D1 0.10ATR: ~0.36%
```

H1 reacts faster and produced slightly stronger annual fresh75 precision in the first probe. D1 produced strong ranking AUC but was too slow in 2026, with large quarterly target-difficulty swings. H4 is therefore the current **balance candidate**, not the winner of an outcome-tuned tournament.

## 5. Slow-N P15 probe result

The first development probe reused the A2-style 86-feature survival representation and used outcome-blind 25-minute de-overlap for training, then scored the full modelable M5 evaluation population.

This is a target-design probe, not a final official model pack.

For `H4_0.25ATR`:

```text
             AUC15    P15>=75 actual hit    fresh75 actual hit
2024         0.8142        82.73%                78.55%   N648
2025         0.7650        81.46%                78.53%   N531
2026 YTD     0.7770        80.58%                76.47%   N323
```

Training-sample phase sensitivity remained similar when the 25-minute de-overlap phase was shifted.

Caveat: quarter-level fresh75 precision is not perfectly flat; e.g. H4 probe 2026Q2 was ~69.75%. Annual stability is encouraging but does not constitute a final freeze.

## 6. What is superseded versus preserved

### Superseded for the active Slow-N strategy line

Do not use these as current authority:

- old N1 = `1.50 * M5 ATR fresh P15 75-cross`;
- old N2-R1 ~57.5% direction accuracy;
- old N3 ATR exit economics;
- old Stoch/tick/M1/Bollinger percentages;
- old trusted-state hierarchy;
- `V8ANP15ContextIndicator.mq5` as an implementation of the new Slow-N concept.

They remain valid records for the old M5-relative population.

### Preserved as methods / hypotheses

Retain and reuse:

- strict chronological purge and causal feature alignment;
- V4 raw-tick UTC wall-clock alignment audit;
- exact-decision tick windows and shifted placebo methodology;
- causal M1 completed-bar and confirmed-swing definitions;
- deterministic Stochastic, MTF and market-question definitions;
- Bollinger state representation;
- disagreement / near-miss comparisons;
- family-wise permutation/multiple-testing audit;
- discovery versus validation discipline.

## 7. Legacy downstream findings to retest, not assume

The strongest old-population hypotheses are retained for **predefined transfer tests** on Slow-N:

1. `M5 Stoch direction D + tick relative 0001` (`NET/MOVE/CLV` opposite D, final `RUN` with D): old N=175, pooled 65.14%.
2. Add `M1 Stoch aligned with M5 Stoch`: old N=57, pooled 71.93%.
3. Stronger M1 Stoch transition subset: old N=40, pooled 75.0%; too small for authority.
4. M1 confirmed structure agreeing with N2-R1: old N=832, N2 accuracy 59.86%.
5. Bollinger BB-A/BB-B/BB-C/BB-D state candidates; all old-population development only.
6. Path-clearance relative `1110` anti-edge and M1-tape relative `0000` anti-edge; post-hoc hypotheses only.

No one of these may be called a Slow-N edge until rerun on the new population.

## 8. Current work order

### S0 — documentation/authority reset
Completed by this package.

### S1 — formalize the slow target contract

1. Rebuild exact causal H1/H4/D1 ATR series from completed bars only.
2. Verify block-boundary semantics and target constancy.
3. Keep `0.25*H4 ATR14` as the provisional primary candidate.
4. Do not tune decimal multipliers on direction/P&L.
5. Compare alternatives only on target meaning, base-rate stability, update cadence and implementation robustness.
6. Freeze the target-scale rule before downstream direction work.

### S2 — rebuild the official Slow-N probability model

1. Keep P15/P30/P60 first-hit survival semantics.
2. Use strict `decision + 60m <= training cutoff` purge.
3. Walk-forward: 2024 from prior data, then 2025, then 2026.
4. Report AUC, Brier, log-loss, calibration, decile ordering and target-distance distributions.
5. Rebuild full, reproducible coefficient/model pack only after architecture is fixed.
6. Verify Python/MQL parity before MT5 authority.

### S3 — freeze the new movement trigger

Profile `P15>=75` and `fresh75` without LONG/SHORT/P&L:

- annual/monthly/quarterly realized movement;
- count and active-day frequency;
- spacing/clustering;
- session distribution;
- target-distance distribution;
- H4-block concentration;
- probability calibration.

Do not use direction outcomes to choose the movement threshold/scale.

### S4 — rerun all downstream direction research on the exact new N1 population

Order:

1. exact transfer diagnostics of frozen legacy rules;
2. deterministic chart-voter / MTF panel;
3. M5 Stochastic;
4. causal M1 structure and transition states;
5. V4-aligned raw tick features and shifted placebo;
6. preregistered Stoch -> M1 -> last-RUN re-synchronization hypothesis;
7. Path-clearance good/bad interaction;
8. Bollinger(20,2) state combinations;
9. multiplicity audit and near-miss comparisons;
10. only after these transfer tests, open genuinely new feature discovery if necessary.

The same 2022-2026 years are already consumed development evidence. A new population does not make them untouched validation.

### S5 — direction freeze, then economics

Only after a direction architecture is frozen:

- preregister Slow-N-consistent SL/TP/exits;
- keep scale fixed according to the same completed-H4 contract during each decision/trade as specified by the exit contract;
- report WR, average winner R, EV, PF, DD, loss streak, holding time, big-winner dependence and execution costs;
- use MT5 Every Tick based on real ticks before any strategy authority.

## 9. Evidence status

```text
2022-2026 = consumed/open development evidence
2024-2026 = heavily consumed by legacy M5-A-N downstream direction research
2021 = LOCKED / UNTOUCHED
```

Do not spend 2021 on target multiplier selection, direction rescue, Bollinger selection or exit tuning.

## 10. Reading authority

Read in this order:

1. `HANDOFF_V8.md`
2. `V8_A_N_SEMANTIC_RESET_AND_SLOW_SCALE_RESEARCH_20260902.md`
3. `V8_A_N_LEGACY_DOWNSTREAM_REVALIDATION_MAP_20260902.md`
4. `DECISIONS_V8_SLOW_N_RESET_ADDENDUM_20260902.md`
5. `RESEARCH_STATE_V8.md`
6. `BACKLOG_V8.md`
7. old `V8_A_N_*_20260901.md` only as historical M5-A-N evidence
8. V8-A/A2/V8-C documents as controls/history when needed.

Always refresh GitHub HEAD before continuing.
