# D-155 — Mentor Fidelity / Opportunity Frequency Audit

Status: `ACTIVE SHADOW-ONLY FIDELITY AUDIT / NO STRATEGY AUTHORITY`  
Date: `2026-08-24`  
Parent: `D154P paused after unstable Entry-filter research`  
2021: `KEEP UNTOUCHED`

## Why this phase

The next question is no longer:

> Which existing trade should be filtered out?

It is:

> Does the deterministic EA recognize the mentor's valid opportunities with the
> same semantics, or did deterministic formalization suppress a material part
> of the opportunity set?

Current GOLD frequency is architecturally stable rather than a one-year anomaly:

```text
2024:
700 PLAN
-> 386 Root contact
-> 309 Sweep
-> 131 current CHOCH
-> 120 FVG branches
-> 61 unique execution geometries
-> 52 Fill

2025:
804 PLAN
-> 466 Root contact
-> 363 Sweep
-> 165 current CHOCH
-> 151 FVG branches
-> 68 unique execution geometries
-> 55 Fill
```

The dominant post-contact choke point is:

```text
Sweep -> current M1 CHOCH
2024: 131 / 309 = 42.4%
2025: 165 / 363 = 45.5%
```

Once a distinct execution geometry exists, most opportunities fill. Therefore
the first fidelity audit targets trigger recognition, not FVG retest execution.

## Source tension that justifies the audit

The mentor-video digest explicitly records that the `three opposite-colour candles`
rule is an experiential wave-recognition aid and should not be promoted as a
universal core law.

The current deterministic contract, however, promoted that rule into the global
wave detector and then made `M1 STRUCTURE_PROTECTED_BREAK` the scenario CHOCH
authority.

This may be a legitimate deterministic approximation, but it has not been
demonstrated that it preserves opportunity frequency.

There is a second operational narrowing:

```text
Root-contact bar cannot satisfy Sweep
```

because closed OHLC cannot establish intrabar contact-before-sweep ordering.
That is conservative and causal, but real-tick testing can tell us how often
same-bar cases exist and whether a later tick-order audit is worth implementing.

## Stage A — no strategy modification

Run GOLD# only:

```text
2024 full year
2025 full year
XM Ultra Low
Every tick based on real ticks
same V3E mode 9 / EM OFF strategy
InpEventLogMode = FULL_AUDIT
```

FULL_AUDIT is logging only.

The runner must reproduce the already-known compact-log strategy counts exactly.
If PLAN/contact/sweep/CHOCH/FVG/geometry/fill counts change, fail closed.

Frozen parity benchmarks:

```text
2024 GOLD#
PLAN       700
CONTACT    386
SWEEP      309
CHOCH      131
FVG        120
GEOMETRY    61
FILL        52

2025 GOLD#
PLAN       804
CONTACT    466
SWEEP      363
CHOCH      165
FVG        151
GEOMETRY    68
FILL        55
```

## Audit population A — Root contact but no accepted Sweep

For every scenario with:

```text
SCENARIO_ROOT_CONTACT_BOUND
and no SCENARIO_SWEEP_ACCEPTED
```

record:

- direction;
- contact time and contact M1 bar;
- terminal time/reason;
- whether FULL_AUDIT contains a direction-compatible `M1_SWEEP_DETECTED`
  on the **same Root-contact M1 bar**;
- number of later compatible sweep detector events before terminal.

Same-bar detector presence is only:

```text
SAME_BAR_SWEEP_CANDIDATE_UPPER_BOUND
```

It is NOT a valid sweep and has no trade authority.

If this population is material, the next audit may use real-tick ordering to
distinguish:

```text
contact -> sweep -> recovery   [potentially source-faithful]
sweep -> contact               [invalid ordering]
ambiguous
```

Do not infer ordering from OHLC.

## Audit population B — accepted Sweep but no current CHOCH

For every scenario with:

```text
SCENARIO_SWEEP_ACCEPTED
and no SCENARIO_CHOCH_ACCEPTED
```

record the window:

```text
Sweep availability -> scenario terminal
```

and count/locate:

```text
M1 STRUCTURE_INITIAL_BOS same direction
M1 STRUCTURE_BOS same direction
M1 STRUCTURE_PROTECTED_BREAK same direction
M5 STRUCTURE_INITIAL_BOS same direction
M5 STRUCTURE_BOS same direction
M5 STRUCTURE_PROTECTED_BREAK same direction
M1/M5 WAVE_CONFIRMED events
```

These are diagnostics only.

Interpretation:

- a material M1 INITIAL_BOS/BOS population would show that the current
  `PROTECTED_BREAK-only` scenario CHOCH definition suppresses existing lower-TF
  structure transitions;
- a material M5-only population would justify manual/video-case review of
  trigger-frame role, not direct M5 order authorization;
- little activity in both M1/M5 would mean the bottleneck lies deeper in
  wave recognition / source reaction semantics rather than only scenario
  acceptance.

## What this audit does NOT do

It does not:

- authorize INITIAL_BOS/BOS as a new Entry trigger;
- authorize M5 direct entries;
- remove the three-candle wave detector;
- allow same-bar Root contact/sweep;
- add INTERNAL_ROTATION;
- change Root, Entry, SL, TP, sizing, SP, EM or FVG selection;
- inspect candidate profitability to select a trigger rule.

The first output is **opportunity accounting**.

## Stage B decision after the result

Only after Stage A:

1. choose the largest source-supported fidelity discrepancy;
2. compare it with mentor-video cases / explicit user interpretation;
3. define one shadow counterfactual;
4. prove OFF/ON non-interference;
5. measure unique physical opportunities gained;
6. only then evaluate Entry survival on a disjoint period.

Potential later audits, not yet authorized:

```text
A. real-tick same-bar Root-contact/sweep ordering
B. mentor-faithful alternative M1 wave/transition recognition
C. role-based M5/M1 trigger-context audit
D. INTERNAL_ROTATION opportunity census
E. omitted liquidity families such as equal-high/low or trendline clusters
```

No arbitrary target trade count is imposed.
The goal is to recover source-valid opportunities, not manufacture frequency.
