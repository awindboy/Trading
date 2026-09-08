# V9 April 2025 Completion and Pipeline Postmortem

Date: `2026-09-09`
Evidence class: `CONSUMED FUTURE-HIDDEN DISCRETIONARY REPLAY + RETROSPECTIVE POSTMORTEM`
Market: `GOLD#`
Production authority: `NONE`

## 1. Boundary and headline ledger

April completed at:

```text
2025-04-30 23:58
```

Closed ledger including P006 carried from March:

```text
32 closed
6 positive / 26 loss
closed sum +62.28R
gross positive +104.56R
gross loss -42.28R
April-new-entry closed sum +32.58R
longest loss streak P018-P028: 11 trades / -13.43R
```

Open at month end:

```text
P038 SHORT 3326.04
legacy accounting ref 3331.29
month-end 3288.42
MTM ~+7.17R
MFE through April 3266.86 / ~+11.27R
```

All R figures are descriptive price accounting from contemporaneous April references, **not** exact Bid/Ask/slippage-adjusted execution economics. The new Hard-SL definition did not exist during these trades and must not be retroactively imposed.

---

## 2. Frozen closed ledger

| Trade | Side | Result | Primary postmortem role |
|---|---|---:|---|
| P006 | LONG | +29.70R | March carry; large winner |
| P007 | SHORT | -2.03R | review-latency contaminated |
| P008 | LONG | -4.55R | review-latency contaminated |
| P009 | SHORT | +0.29R | MFE ~+15.6R giveback |
| P010 | SHORT | -1.00R | Child invalidation |
| P011 | SHORT | -1.72R | Child invalidation |
| P012 | SHORT | -1.33R | repair-failure loss |
| P013 | SHORT | -1.54R | repair-failure loss |
| P014 | SHORT | -1.19R | repair-failure loss |
| P015 | LONG | -0.86R | Child origin lost |
| P016 | SHORT | -2.96R | review-latency contaminated |
| P017 | LONG | +16.77R | large Parent winner |
| P018 | SHORT | -1.93R | shock reversal counterexample |
| P019 | LONG | -2.21R | same-auction cluster |
| P020 | SHORT | -1.36R | same-auction cluster |
| P021 | LONG | -0.69R | same-auction cluster |
| P022 | LONG | -1.32R | same-auction cluster |
| P023 | LONG | -0.49R | same-auction cluster |
| P024 | LONG | -1.24R | failed continuation |
| P025 | SHORT | -1.29R | failed repair thesis |
| P026 | LONG | -1.11R | failed continuation |
| P027 | SHORT | -0.59R | rapid repair |
| P028 | LONG | -1.20R | failed launch before P029 |
| P029 | LONG | +24.17R | new business -> large winner |
| P030 | SHORT | -2.36R | review-latency contaminated |
| P031 | LONG | +23.05R | large Parent winner |
| P032 | SHORT | +10.58R | large lower journey |
| P033 | SHORT | -1.32R | repair failure failed |
| P034 | LONG | -0.98R | retest failed |
| P035 | SHORT | -1.45R | MFE ~+4.1R -> loss |
| P036 | SHORT | -4.39R | MFE ~+11.4R -> loss; review latency |
| P037 | LONG | -1.17R | MFE ~+2.6R -> loss |

---

## 3. What April supports

### A. Large Parent-Journey capture was repeatable inside consumed evidence

Large positive examples:

```text
P006 +29.70R
P017 +16.77R
P029 +24.17R
P031 +23.05R
P032 +10.58R
```

This matters because March's large winners were not isolated to a single episode. The revised Parent/Child separation allowed local entry and multi-H1/H4 participation.

This is promising, not validated. The payoff remains concentrated in a small number of trades.

### B. Baseball payoff shape is real but fragile

Only 6/32 closed trades were positive, yet the closed sum was strongly positive because the large winners dominated. Removing the three largest positives would leave the month negative.

Therefore the strategy's survival depends on:

- staying available for genuine large journeys;
- not allowing same-auction losses to explode;
- not giving large winners back unnecessarily.

---

## 4. Problem situation: review latency made risk accounting unreal

Several trades were explicitly contaminated by delayed review. P008 and P036 were the clearest examples of a nominal structural reference being exceeded materially before the next discretionary check.

Diagnosis:

```text
accounting reference != actual maximum risk
```

Correction accepted after April:

```text
precommitted Hard SL before entry
+ Hard SL touch terminates Child
+ never widen
+ manual structural exit may occur earlier
```

This is an execution/risk correction, not a fixed market stop formula.

---

## 5. Problem situation: same auction repeatedly relabeled as a new Child

P019-P023 formed a clear loss cluster. Each micro thesis had local logic, but the higher-scale market repeatedly repaired both directions in the same broad auction.

Correction:

Before another same-side attempt, state exactly what new business/information exists now that did not exist when the prior Child failed.

Do not use N-loss limits or cooldowns. The discriminant is market-state change, not attempt count.

---

## 6. Problem situation: failed attempts vs eventual large winner

Matched family:

```text
P024 LONG loss
P026 LONG loss
P028 LONG loss
P029 LONG +24.17R
```

The useful difference was not `P029 was the fourth try`.

P029 followed a more developed sequence of new business, repeated hold, departure, and reuse/return behavior. The earlier attempts were closer to incomplete or same-auction continuation hypotheses.

May research must record `WHAT IS NEW?` contemporaneously so this distinction can be tested without hindsight.

---

## 7. Problem situation: winner continuation became too passive in some cases

Mandatory giveback evidence:

```text
P009  MFE ~+15.6R -> +0.29R
P035  MFE ~+4.1R  -> -1.45R
P036  MFE ~+11.4R -> -4.39R
```

The earlier error was exiting every micro anchor. The new opposite error is occasionally waiting too long for definitive Parent death while progression ability is already deteriorating.

Correction direction:

- monitor Parent campaign health on completed H1;
- focus on favorable-extreme progression, settlement migration, counterflow business, repair success/failure, memory consumption;
- tighten to M15 when deterioration becomes material;
- do not use fixed R locks or claim to know the final top/bottom.

---

## 8. Retrospective H1 indicator exploration

This section is **discovery only** because April is already consumed.

Using H1 Stochastic(14,3,3), cross **location** is a plausible variable to study rather than treating every cross identically. For example, P035 experienced a golden cross deep in the oversold area during the later repair sequence. P009 also showed an oversold-region golden cross before the short campaign's large giveback. These examples do **not** establish that extreme-zone crosses are stronger than mid-range crosses.

But strong winners supplied decisive counterexamples: P017/P029/P031 experienced multiple adverse dead crosses in/above overbought territory and still extended materially.

Therefore:

```text
extreme-zone adverse cross = possible attention/warning event
!= automatic exit
```

The stronger prospective question is whether an extreme-zone adverse cross is followed by:

```text
failure to make a new favorable extreme
+ failed oscillator re-acceleration
+ adverse H1 settlement/value migration
```

H1 EMA9 relation is retained as another shadow descriptor. H4 crosses appeared too slow for this consumed sample.

No indicator is promoted to entry or exit authority.

---

## 9. April conclusions carried into May

Keep:

- Parent/Child separation;
- repeated participation after genuinely new information;
- local precision with larger lifecycle;
- no chase after missed leg;
- no nearest-memory automatic TP;
- no fixed profit target.

Change:

- make Hard SL real before entry;
- require explicit new information for retries;
- monitor H1 campaign health systematically;
- collect H1 Stochastic cross location/re-acceleration and EMA9 only as shadow evidence;
- review every completed H1 while a Parent-Journey position is open.

Do not formalize from April alone.

---

## 10. Causal-integrity exceptions recorded during April replay

Two tooling/operation incidents were detected and explicitly contained rather than silently repaired:

1. After the `2025-04-10 22:30` boundary, one inspection accidentally exposed M1 through `2025-04-11 06:00`. No hindsight trades were inserted inside that exposed interval; clean causal decision-making resumed from `2025-04-11 06:00`.
2. An uploaded higher-timeframe row was briefly inspected before recognizing that an unfinished H4 row contains later minutes. That incomplete H4 value was discarded from decision authority. From then on, uploaded M5/M15/M30/H1/H4 files are usable only for **fully completed bars behind the current M1 cutoff**; current partial bars are reconstructed from revealed M1.

These incidents are process evidence. They do not justify rewriting any frozen trade outcome.

