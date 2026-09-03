# V8 Decisions — Executable Mapping Revalidation Addendum

Date: `2026-09-03`
Status: `ACTIVE AUTHORITY ADDENDUM`
Source Git HEAD verified: `636524efc0335b1569405cfed420e84549a0c4b9`

## D-V8-EM-001 — GOLD-only research freeze

Decision:

- Do not research, validate, transfer, shortlist, or trade-test any market other than `GOLD#` until the user explicitly reopens other markets.
- Existing USDJPY#/XAUEUR#/BTCUSD source-of-move and market-universe documents remain historical/preregistered context only.
- `GOLD# 2021` remains untouched.

Reason:

The user explicitly requires completion of the GOLD strategy before any other-market branch.

---

## D-V8-EM-002 — P0/P2 are training de-overlap realizations, not execution phases

Decision:

`P0` and `P2` represent alternate deterministic training-sample offsets. Model inference/fresh75 generation occurs across the full modelable M5 population.

Do not describe P0 as “trade only m5_index % 5 == 0” or P2 as “trade only m5_index % 5 == 2”.

P2 remains robustness evidence and must not be merged opportunistically with P0 into one account.

Reason:

The current P0 fresh75 population is distributed across all M5 residues. The prior interpretation that the account replay only traded one-fifth of decisions was incorrect.

---

## D-V8-EM-003 — Statistical discrimination must be paired with executable mapping evidence

Decision:

When a V8 result reports AUC or similar prediction quality for a state intended to influence trading, the same report must include the tested executable mapping and trading outcome if such a mapping exists.

Minimum reporting:

```text
target semantics
information availability time
action rule
N
WR
mean R / expectancy
PF
average winner/loss when meaningful
year split
status: descriptive/shadow/diagnostic/challenger/control
```

If no executable mapping exists, write `NO EXECUTABLE TRADING RESULT YET`.

Reason:

High AUC for structural retention or future High-Q state does not automatically imply profitable entry/exit permission.

---

## D-V8-EM-004 — Do not promote micro3 from structural-quality prior to direct Base permission

Decision:

Preserve `micro3 = prog1 + run_accept + prog3` as an acceptance-time structural-retention ranking prior.

Do not use high micro3 alone as a proven direction/economic Base filter.

Current revalidation:

- retention AUC about `.729` in 2025 and `.735` in 2026;
- representative Q75 Base mapping: N90 combined, WR `44.4%`, mean `-0.111R`, PF `0.800`.

Reason:

The target being predicted is structural retention, not Base TP-before-SL economics. The executable mapping failed even though the structural target remains predictable.

---

## D-V8-EM-005 — Do not equate close damage with automatic exit

Decision:

Preserve `CLOSE_BROKEN` as a serious structural-hazard state.

Do not freeze `CLOSE_BROKEN -> immediate next-open exit` as a trading rule.

Current diagnostic across 668 Base events:

- WR about `38.5%`;
- mean about `-0.043R`;
- PF about `0.900`;
- average loss improves, but expectancy is worse than Base.

Reason:

Structural hazard and optimal exit are separate research layers.

---

## D-V8-EM-006 — Routine Base is a negative economic control, not the V8 edge

Decision:

The current routine Base remains control-only:

```text
ACCEPTANCE -> next M1 open -> +0.25S / -0.25S
```

Current 668-event P0 result:

- WR `48.5%`;
- mean about `-0.029R`;
- PF about `0.944`;
- chronological account contribution about `-$31.85`.

Do not describe the current Base as a profitable V8 component.

Reason:

The combined account replay was profitable because the High-Q runner offset Base losses.

---

## D-V8-EM-007 — Preserve the High-Q runner as the strongest positive executable component

Decision:

Preserve the t15 close-intact + realized-progress runner as positive development evidence:

```text
ACCEPTANCE +15m
close integrity intact
MFE15 >= 0.555S
-> next M1 open
-> +0.75S TP / -0.40S SL
```

P0 fixed-0.01 diagnostic:

- N61;
- WR `49.18%`;
- mean about `+0.287R`;
- PF about `1.68-1.71`;
- average winner about `+1.4R`;
- positive mean R in 2024, 2025 and 2026.

P2 robustness:

- N70;
- WR about `51.4%`;
- mean about `+0.214R`;
- PF about `1.53-1.56`.

This is not production authority because sample size is limited and P0 aggregate WR is below the final >=50% requirement.

---

## D-V8-EM-008 — ACCEPTANCE may be an observation state rather than paid Base entry

Decision:

Do not assume every ACCEPTANCE requires immediate capital deployment.

Current evidence permits the research semantics:

```text
ACCEPTANCE = start causal observation / state tracking
capital authorization = later executable evidence, if validated
```

Reason:

Runner-only 60m control approximately matched/exceeded the full wrapper return while cutting drawdown materially, whereas routine Base was negative.

This is a research direction, not yet a frozen final policy.

---

## D-V8-EM-009 — Active bottleneck is action/exposure mapping through the early path

Decision:

The immediate GOLD-only research question is not another generic indicator family.

It is the causal action/exposure mapping through:

```text
fresh75
-> reveal
-> pullback
-> ACCEPTANCE
-> 1-10m path/state
-> runner-grade realized progress
```

Research must preserve Base as control and separate:

- direction permission;
- structural hazard;
- entry timing;
- early abort/reduction;
- confirmation/add;
- exit/payoff;
- capital sizing.

Prefer shadow-only economic bridge audits before changing execution.

Reason:

V8 already has evidence for movement onset, structural-state estimation and winner continuation, but has not yet converted those layers into one high-frequency, high-payoff, cost-positive policy satisfying the final targets.
