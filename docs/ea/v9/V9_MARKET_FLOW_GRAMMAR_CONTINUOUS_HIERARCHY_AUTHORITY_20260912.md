# V9 Market Flow Grammar — Continuous Hierarchy Authority

Date: `2026-09-12`
Status: `ACTIVE V9 RESEARCH AUTHORITY / CONTINUOUS HIERARCHICAL MARKET-FLOW GRAMMAR`
Market: `GOLD# ONLY`
Production authority: `NONE`
EA authority: `NONE`

Consumed answer-sheet data:

- `2025-01 through 2025-06`
- `2026-01 through 2026-02`

Locked / untouched:

- `2025-07 LOCKED`
- `GOLD# 2021 untouched reserve`

Authoritative M1 SHA256:

`626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`

GitHub base HEAD used for this research bundle:

`b7ad4da10383699a38434a163a5e8e72db15b5d5`

---

## 1. Why this authority exists

The project must not return to the old loop:

```text
trade fails
-> explain one case
-> add one filter
-> another case fails
-> add another filter
```

The active research objective is not to discover a rare high-probability setup.

The objective is to explain the **continuous price process** with the smallest reusable grammar possible, then reverse-engineer a tradable subset later.

Current market model:

```text
larger state
-> local auction
-> arrival / landmark
-> response / interruption
-> delivery or authority erosion
-> next state
-> repeat
```

POI, OB, FVG, liquidity, MSS, sessions, indicators, and LTF patterns are not independent strategy authorities.
They are candidate observations inside the continuous flow.

---

## 2. Current minimal hierarchy

### H4 macro authority

```text
STRONG DIRECTIONAL
WEAK DIRECTIONAL
NEUTRAL / AMBIGUOUS
```

`STRONG / WEAK` is a research representation of agreement among multiple causal H4 views.
It is not a live-entry threshold.

Important principle:

> uncertainty is itself market-state information.

Do not add another indicator merely to force a weak/ambiguous map into UP or DOWN.

### H4 phase

Core phase:

```text
MIGRATION
LOCAL_INTERRUPT
NEUTRAL
```

`LOCAL_INTERRUPT` may be described as pause-like, repair-like, or unresolved, but these are modifiers rather than separate strategy branches.

### H1 inner auction

Inside directional H4 authority:

```text
ALIGNED
H1_INTERRUPT
```

`H1_INTERRUPT` intentionally merges H1 counterflow and local balance at the top-level grammar.

### Landmarks

Exact objects remain important as coordinates:

```text
POI
FVG
OB candidate
liquidity / swing candidate
object creation / consumption / invalidation
```

But:

```text
LANDMARK != FLOW STATE
LANDMARK != ENTRY SIGNAL
```

---

## 3. Broad consumed-data evidence

After strict in-period warmup and strict information-known boundaries:

### H4 representation coverage

```text
2025-01..06
703 completed research H4 bars after warmup
exact role majority coverage: 83.9%
macro-state majority coverage: 95.4%
time in MIGRATION: 66.3%

2026-01..02
188 completed research H4 bars after warmup
exact role majority coverage: 85.1%
macro-state majority coverage: 98.4%
time in MIGRATION: 73.4%
```

The goal is not 100% forced coverage.
Unexplained/disputed remainder stays explicit.

### H4 migration interruption topology

Strict final ledger:

```text
2025: 66 interruption episodes
2026 Jan-Feb: 17
```

Normal topology is:

```text
MIGRATION
-> LOCAL_INTERRUPT
-> usually SAME MIGRATION or NEUTRALIZATION
```

Direct immediate opposite-side transition is uncommon.

### Actual directional side changes

```text
2025: 33
2026 Jan-Feb: 8
```

Most side changes traverse an intermediate transition buffer rather than one exact reversal vertex.
Earlier analysis found a median transition buffer near 12 hours and a high use of neutral/ambiguous states.

---

## 4. H1 nested auction — the recurring flow unit

Consensus H1 interruption cycles:

```text
2025: 145
2026 Jan-Feb: 41
```

The common path is:

```text
H4 directional authority
-> H1 aligned
-> H1 interruption
-> H1 realign
```

before the H4 side itself changes.

Consensus realignment frequency:

```text
2025: 76.6%
2026 Jan-Feb: 78.0%
```

This is **not a trade win rate**.
It is a descriptive property of nested timescales.

Cross-view robustness:

```text
3 causal H4 state views
x
3 causal H1 state views
= 9 combinations per block

2025 H1 realignment range: 71.5% to 91.2%
2026 Jan-Feb:              76.9% to 89.6%
```

Therefore the topology matters more than any specific EMA/lookback implementation.

---

## 5. State confidence is part of the grammar

At H1 interruption start, the larger H4 side may be strongly or weakly represented.

Earlier consumed-data study showed:

```text
3/3 H4 side agreement
2025 realign: 84.3%
2026 realign: 82.4%

2/3 H4 side agreement
2025 realign: 54.1%
2026 realign: 57.1%
```

Do not convert `3/3` into a mechanical entry gate.

Interpretation:

> the same local counterflow has a different meaning when the slower directional authority is already internally disputed.

This is more important than adding generic MACD / BB / PD / session confirmations.

---

## 6. Difficult month result — 2025-05

2025-05 is not a special exception and does not require a May-specific rule.

Compared with the other consumed 2025 months, May had:

```text
less strong H4 authority
more weak H4 authority
more H4 local interruption
more H4 neutral time
more H1 interruption
more actual H4 side changes
slower H1 cycle resolution
```

Key strict figures:

```text
strong H4 authority within directional time
May:   74.0%
other 2025 months mean: 80.9%

H4 local-interruption share
May:   32.3%
others: 23.8%

H1 realign rate
May:   59.3%
others mean: 80.8%

median H1 interruption bars to resolution
May: 5.0
others mean: 3.7

directional side changes
May: 9
others mean: 4.8
```

Within May itself:

```text
H4 3/3 side agreement:
20 H1 cycles, 75.0% realign

H4 2/3 side agreement:
7 H1 cycles, 14.3% realign
```

Do not use those small-subset percentages as strategy thresholds.
The point is that the existing grammar explains why May was transition-heavy.

---

## 7. UNRESOLVED is legitimate information

`UNRESOLVED_UP / DOWN` means:

```text
directional macro majority still exists
but exact role (migration / pause / repair) is disputed
```

When UNRESOLVED emerged directly from migration:

```text
2025: 34 cases
67.6% -> same migration
23.5% -> neutralized
 8.8% -> opposite side

2026 Jan-Feb: 11 cases
54.5% -> same migration
36.4% -> neutralized
 9.1% -> opposite side
```

Therefore UNRESOLVED should not be forcibly relabeled as migration or reversal.

---

## 8. AMBIGUOUS must remain non-directional

`AMBIGUOUS` means no H4 directional macro majority exists across the three causal views.

2025 ambiguous episodes with a prior direction:

```text
22 episodes
next migration same as prior:     11
next migration opposite to prior: 11
```

That is exactly 50 / 50 in the consumed 2025 sample.

Do not invent a tiebreaker.

2026 had only three comparable cases and all went opposite; the sample is too small to override the 2025 conclusion.

Principle:

> when the representation has no directional authority, preserve that uncertainty and let the next migration earn authority.

---

## 9. Critical research corrections

### 9.1 Early acceptance/rejection numbers

Some early 80-90% results reused part of the classification window in the subsequent movement measurement.
They are descriptive answer-sheet coverage, not forward predictive edge.

They must not be cited as strategy performance.

### 9.2 Balance accepted-probe result

The earlier ~94% `last accepted probe before the next directional state` result was hindsight-selected because it chose the last probe using the later state transition.

A causal all-probe audit did not preserve that result.

Do not use the 94% figure as authority.

### 9.3 Session / generic ICT confirmation expansion

The following were tested enough to stop as active research directions:

- session label alone;
- generic London/NY sweep -> reclaim -> body-break;
- generic MSS;
- fresh FVG confirmation;
- breaker/inversion auto-role flip;
- premium/discount alone;
- MACD / Bollinger confirmation;
- fixed double-sweep count;
- high-velocity/low-occupancy as a standalone forward classifier.

Do not continue stacking these unless later continuous-flow evidence independently reopens the question.

### 9.4 Rare repair-resumption subset

The earlier small-sample `repair + POI + H1 support response` result was useful as a clue but is no longer the research target.

Do not optimize around rare 80-90% subsets.

### 9.5 July boundary correction

A working ledger once retained a source bar dated June 30 whose **information-known time** was exactly July 1 00:00.

Final authority rule:

```text
2025 consumed state/event known_at < 2025-07-01 00:00
```

The strict final scripts enforce this.

---

## 10. Research method from now on

### Use continuous coverage, not setup mining

Evaluate:

```text
how much time the grammar describes
how transitions resolve
whether the same topology survives alternate causal state views
whether difficult months are explained without exceptions
```

### Preserve uncertainty

Allowed states include:

```text
WEAK
UNRESOLVED
AMBIGUOUS
NEUTRAL
```

Do not create rules merely to eliminate these labels.

### Prefer state transitions over event counts

POI/liquidity counts may describe structural churn.
They must not become hidden thresholds such as:

```text
N touches
N sweeps
N hours
N FVGs
```

unless a future preregistered study independently earns that authority.

### Use multiple causal views for robustness

A concept is more valuable if the topology survives different reasonable state representations.
Do not optimize one lookback for maximum historical fit.

### Keep answer-sheet and causal phases separate

Current Atlas work may inspect consumed future history.

It must never be reported as:

- validation;
- realized strategy expectancy;
- causal trade performance.

The final extracted strategy must later survive sequential future-hidden replay.

---

## 11. What the next session should research

Do **not** search for new indicators or rare filters first.

Continue in this order:

### A. Route / destination inside the normal cycle

Study the full common sequence:

```text
H4 authority
-> H1 interrupt
-> H1 realign
-> next delivery
-> next meaningful POI/liquidity arrival
```

Questions:

- what is the natural destination of the resumed H1 auction?
- which landmark is transit versus campaign-changing?
- how many successive H1 child auctions normally occur inside one H4 campaign?
- when does a delivered liquidity event merely create the next repair rather than terminate the Parent?

Do not optimize TP yet.

### B. Parent continuity versus authority loss

Build an explicit ledger distinction:

```text
SAME PARENT / NEXT H1 AUCTION
vs
PARENT AUTHORITY LOST / AUCTION RESET
```

Use H4 confidence erosion / neutralization as the primary evidence.
Do not use one child stop or one MSS as Parent invalidation.

### C. Exact landmark roles

Attach exact object IDs to continuous cycles:

```text
origin landmark
delivery landmark
transit landmark
campaign-changing landmark
```

Use the object engine for geometry and lifecycle.
AI may assign semantic role later.

### D. Only then prepare strategy extraction

When route/destination and Parent-continuity semantics are compact enough, freeze a **strategy-extraction draft** before any future-hidden replay.

---

## 12. Things the next session must not do

Do not:

- reopen July;
- use 2021;
- tune Entry/SL/TP because one subset looks good;
- optimize a state lookback for highest accuracy;
- create a daily trade quota;
- create a fixed duration/cooldown/retry rule;
- force AMBIGUOUS into UP/DOWN;
- make MACD/BB/session/PD-array mandatory confirmation;
- promote FVG/OB existence into strategic importance;
- confuse descriptive 80-90% answer-sheet coverage with forward alpha;
- backfill a trade from known future movement;
- treat a Child result as automatic Parent validation/invalidation;
- change authority from one or two examples.

---

## 13. One-line current V9 research model

> GOLD is treated as a nested continuous auction: slower H4 authority contains repeated H1 interruptions and realignments until larger authority erodes, neutralizes, and a new migration earns control; POI and liquidity are exact landmarks inside that process, not standalone setups.
