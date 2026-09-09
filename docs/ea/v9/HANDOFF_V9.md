# V9 Development Handoff

Last updated: `2026-09-09`
Status: `ACTIVE V9 / MAY CONSUMED / JUNE AUDITABLE-DISCRETION PREP`
Current phase: `MAY HARNESS POSTMORTEM -> JUNE 2025 FUTURE-HIDDEN REPLAY`
Production authority: `NONE`
EA authority: `NONE`
Market: `GOLD# ONLY`
Untouched reserve: `GOLD# 2021`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`

## 1. Resume order

Start every new V9 session from GitHub.

Read in this order:

1. latest Git HEAD;
2. root routing docs only as needed;
3. `docs/ea/v9/AGENTS_V9.md`;
4. this file;
5. `docs/ea/v9/RESEARCH_STATE_V9.md`;
6. `docs/ea/v9/DECISIONS_V9_APR25_PIPELINE_ADDENDUM_20260909.md`;
7. `docs/ea/v9/DECISIONS_V9_MAY25_HARNESS_ADDENDUM_20260909.md`;
8. `docs/ea/v9/results/V9_APR25_COMPLETION_AND_PIPELINE_POSTMORTEM_20260909.md`;
9. `docs/ea/v9/results/V9_MAY25_COMPLETION_AND_HARNESS_POSTMORTEM_20260909.md`;
10. `docs/ea/v9/V9_DISCRETIONARY_TRADING_PIPELINE_JUN25_20260909.md`;
11. `docs/ea/v9/V9_NEXT_RESEARCH_CONTRACT_JUN25_AUDITABLE_DISCRETION_20260909.md`;
12. stable mindset/manual-replay docs for retained vocabulary/history;
13. raw-data cutoff state before any future reveal.

Old May pipeline/contract are historical consumed evidence, not current June authority.
V10 is separate.

---

## 2. Permanent objective

```text
market understanding
!=
direction prediction
!=
good trade
```

Build a trader that selects worthwhile pitches under uncertainty, accepts bounded Child losses, preserves Parent context appropriately, and participates materially in large journeys.

Do not optimize for predicting every move.

---

## 3. May changed the upstream diagnosis

Before May, major active problems were:

- real Hard SL;
- same-auction / Child independence;
- campaign-health giveback.

May first pass then produced:

```text
24 May-new trades
5 positive / 19 loss
net -6.66R
LONG / SHORT = 1 / 23
```

The month contained large two-sided Parent Journeys, so the absence of large winners could not be explained only by lack of opportunity.

Retrospective second-pass strategy-compliance replay produced a radically different implementation:

```text
15 trades
12 positive / 3 loss
about +51.37R descriptive
LONG / SHORT = 7 / 8
```

But the second pass already knew May outcomes and is **not validation**.

The reliable conclusion is process-level:

```text
same high-level strategy
!=
same discretionary execution
```

---

## 4. Main first-pass drifts

### A. Directional inertia

Parent working belief became a de facto directional preference. Upward opportunities and bearish counterflow were not always evaluated symmetrically.

Correction: every serious candidate now records continuation and opposite/inversion cases plus `WHY THIS SIDE / WHY NOT OPPOSITE` and a mirror check.

### B. `NO CHASE` became an implicit gate

`Already moved`, nearest memory, and immediate route-room sometimes acted like an unauthorized minimum-R veto.

Correction: these remain context but cannot reject a Parent-Journey opportunity without stating the actual structural reason.

### C. New Child was treated too much like good pitch

Correction:

```text
INDEPENDENT CHILD != WORTHWHILE PITCH
```

Both questions must be answered before entry.

### D. Parent-Journey ambition became too local

Correction: Local Bridge remains valid only when the actual thesis is local. Coherent Parent + meaningful Child requires explicit Parent-Journey consideration.

---

## 5. Stable risk/lifecycle decisions retained

Hard SL remains mandatory for every new trade:

- frozen before entry;
- real Child falsification;
- never widened;
- touch ends Child;
- later same-direction movement cannot rescue it;
- Parent is reassessed separately;
- manual structural exit can occur earlier.

No fixed ATR/R stop/TP, automatic BE, partial, or trail.

---

## 6. New compliance-harness principle

Strategy and harness are now explicitly separate.

The harness is not a signal generator.

It requires each session to expose:

- two-sided Parent context;
- Child role and independence;
- why the pitch is worth taking;
- strongest counterevidence;
- why this side and not opposite;
- Hard SL meaning;
- intended journey scale;
- mirror/hidden-veto check;
- serious candidate `TRADE/NO TRADE` reason;
- layer-specific exit evidence;
- end-of-session bias/process audit.

This should reduce black-box drift without defining a numeric market model.

---

## 7. June exact start state

May data ends:

```text
2025-05-30 23:57
POSITION: FLAT
```

First June print exists at:

```text
2025-06-02 01:00
```

Do not reveal its price until the June contract's **preflight contamination audit** is completed.

No June price outcome has current strategy authority merely because the full raw file exists.

---

## 8. June operational rule

Use:

`V9_DISCRETIONARY_TRADING_PIPELINE_JUN25_20260909.md`

Once the first June price is revealed, freeze that harness for the month.

Do not patch the live June process from wins/losses. Log possible defects as `HARNESS SHADOW ISSUE` for post-June review.

---

## 9. What must not regress

Do not return to:

- Child stop = Parent death;
- Parent as one-side-only veto;
- Child independence = automatic trade permission;
- same-auction repeated relabeling;
- implicit min-R / nearest-memory filter;
- automatic `already moved too much` rejection;
- Local Bridge default because Parent holding is uncertain;
- passive Parent hold after real deterioration;
- fixed indicator exits;
- fixed profit locks;
- forced LONG/SHORT balance;
- hindsight rescue or backfill;
- mid-month process repair from outcome pressure.

---

## 10. Immediate next task

Before June trading:

1. verify latest HEAD contains the May harness addendum and June pipeline/contract;
2. perform repo-wide/document preflight for any known June outcome references;
3. verify authoritative M1 hash;
4. initialize exact cutoff at `2025-05-30 23:57`, flat;
5. reveal only the first causal June prefix under the frozen June harness.

Primary June research question:

> Can V9 produce auditable, cross-session-consistent discretionary decisions without overformalizing the market strategy?

Formalization gate remains closed.
