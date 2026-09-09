# V9 May 2025 Completion and Harness Postmortem

Date: `2026-09-09`
Status: `MAY COMPLETE / FIRST PASS RETAINED / SECOND PASS RETROSPECTIVE AUDIT / JUNE HARNESS REVISION`
Market: `GOLD# ONLY`
Production authority: `NONE`
EA authority: `NONE`

## 1. Evidence classification

May now contains two distinct replays. They must never be merged into one performance ledger.

### First pass

- operationally sequential/causal during most of the month;
- contained known qualitative contamination on May 5/6 and May 12;
- contained several explicit coarse-reveal / future-exposure incidents that were frozen with no backfill;
- later postmortem found material **strategy-compliance drift** in discretionary interpretation.

First-pass May-new summary:

```text
24 trades
5 positive / 19 loss
net -6.66R
LONG / SHORT = 1 / 23
best May-new trade = +3.18R
```

This remains historical evidence of the first implementation. Do not delete or rewrite it.

### Second pass

- performed only after the entire May outcome was known;
- explicitly retrospective and outcome-contaminated;
- purpose was to test whether the same V9 authority could be applied in a more internally consistent and auditable way;
- **not future-hidden and not validation evidence**.

Second-pass descriptive summary:

```text
15 trades
12 positive / 3 loss
net about +51.37R
LONG / SHORT = 7 / 8
large Parent captures included about +13.73R, +8.28R, +6.74R
```

Do not promote these numbers as achievable prospective performance.

---

## 2. What the divergence means

The important result is not `-6.66R versus +51.37R`.

The important result is:

```text
same high-level V9 language
-> materially different discretionary implementation
-> materially different participation and P/L
```

This demonstrates a harness problem:

```text
having rules in documents
!=
a session actually applying those rules consistently
```

The next authority revision must therefore control **decision-process compliance** without over-specifying market patterns.

---

## 3. First-pass process drifts

### A. Directional asymmetry

First pass became almost a SHORT-only implementation:

```text
LONG 1
SHORT 23
```

This was not explained by an explicit one-sided market prohibition. Upward Parent opportunities were often treated more skeptically than bearish counterflow opportunities.

Diagnosis:

- Parent working belief gained directional inertia;
- opposite-side evidence was not always evaluated with the same standard;
- counterflow Child evidence was sometimes promoted too quickly into Parent-route change.

Correction: mandatory two-sided Parent case + `WHY THIS SIDE / WHY NOT OPPOSITE` + mirror check.

### B. `NO CHASE` drifted into a hidden minimum-R / nearest-memory veto

First pass repeatedly rejected candidates because price had already moved or the nearest known high/low was too close relative to the proposed stop.

This sometimes contradicted existing V9 authority:

- no fixed minimum-R entry filter;
- nearest memory is not automatic full TP;
- Parent-Journey participation may continue through checkpoints.

Correction: prior movement and nearest route-room are context, not automatic vetoes. The trader must explain the current Child's role and the intended journey, rather than use an undocumented geometry threshold.

### C. Child independence was confused with pitch quality

The first pass did improve documentation of `WHAT IS NEW?`, but many entries effectively became:

```text
new business exists
+ repair fails
=> trade
```

This proves independence more readily than trade quality.

Correction:

```text
INDEPENDENT CHILD
!=
WORTHWHILE PITCH
```

A future session must explicitly answer both.

### D. Parent-Journey ambition shrank

First pass frequently used Local Bridge logic or local destination geometry even though V9's stated objective is material Parent participation.

This can make the strategy safe-looking but structurally unable to recreate its large-winner architecture.

Correction: Local Bridge remains valid only when the thesis itself is local. A coherent Parent + meaningful Child must trigger explicit consideration of Parent-Journey participation.

---

## 4. What should NOT be copied from the second pass

The second pass is not a template of exact entry patterns.

Do not promote from it:

- `repeated hold` as a mandatory N-hold rule;
- `departure + return test` as a required sequence;
- any exact M15/H1 count before entry or exit;
- any specific R or point threshold;
- any specific May stop distance;
- any exit after exactly N adverse settlements;
- a requirement for balanced LONG/SHORT counts.

Those would convert retrospective examples into overfit pattern rules.

The second pass is useful only for identifying **process invariants**:

- symmetric directional evaluation;
- explicit pitch-quality reasoning;
- no hidden vetoes;
- real Parent-Journey ambition;
- layer-specific exit evidence;
- auditable candidate rejection.

---

## 5. Hard SL conclusion remains intact

May first pass still supports Hard SL as an operational risk-control correction:

- every new trade had a precommitted maximum price-risk boundary;
- Hard SL was never widened;
- stop touch ended the Child;
- April-style review-latency overshoot was prevented.

This is process-control evidence, not proof of entry edge.

Keep Hard SL unchanged for June.

---

## 6. Parent/Child separation conclusion remains intact

Both passes reinforce:

```text
invalid Child != invalid Parent
later same-direction movement cannot rescue stopped Child
Parent survival alone != permission to retry
```

New information remains necessary for a new Child, but the May comparison adds:

```text
new Child != good pitch
```

This becomes a permanent distinction.

---

## 7. Campaign-health conclusion

Campaign-health remains useful but discretionary.

The first pass produced both:

- useful early structural exits;
- severe MFE giveback before deterioration was recognized.

The second pass showed that larger Parent participation can coexist with campaign-health exits when the trader does not downgrade every counterflow into immediate Parent death.

No fixed profit lock, trailing multiple, oscillator exit, or N-bar settlement rule is earned.

June must keep the same qualitative progression questions and require the exit rationale to name which scale/layer is actually deteriorating.

---

## 8. New primary research problem

Before May, the dominant open questions were:

- bounded risk;
- Child independence;
- campaign-health giveback.

After comparing the two May passes, a new upstream problem is explicit:

> Can a discretionary AI trader execute the same strategy with auditable consistency across sessions without turning the strategy into a rigid threshold system?

This is `HARNESS / DECISION-COMPLIANCE RESEARCH`.

The strategy and harness must remain separate:

```text
STRATEGY
= market meaning, hierarchy, risk, opportunity, lifecycle

HARNESS
= required questions, symmetry checks, hidden-veto detection, candidate audit, state persistence
```

The harness may constrain how reasoning is performed and recorded. It must not invent new market edges.

---

## 9. June carry-forward

Retain unchanged:

- Role > Pattern;
- Parent/Child separation;
- real pre-entry Hard SL;
- no rescue after stop;
- no automatic BE/partial/trail;
- no fixed minimum-R filter;
- no Parent direction veto;
- WHAT IS NEW? for same-side retry;
- H1 campaign-health monitoring;
- Stochastic/EMA shadow-only;
- causal prefix discipline;
- formalization gate closed.

Add for June:

- two-sided Parent/opposite case at serious candidate review;
- `WHY THIS SIDE NOW? / WHY NOT OPPOSITE?`;
- `INDEPENDENT CHILD != WORTHWHILE PITCH`;
- mirror/symmetry audit;
- hidden-veto audit;
- serious-candidate rejection log;
- explicit Local Bridge vs Parent-Journey ambition check;
- layer-specific discretionary exit rationale;
- session-level compliance self-audit;
- frozen harness for the entire June replay.

---

## 10. Status

May is consumed development evidence.

The second pass is retained only as retrospective harness evidence.

Neither pass is independent validation.

June must begin under the new frozen auditable-discretion harness before any June price reveal.
