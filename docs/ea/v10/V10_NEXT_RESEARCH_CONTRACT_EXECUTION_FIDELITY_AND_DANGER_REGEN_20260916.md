# V10 Next Research Contract — Execution Fidelity First, Then Danger/Persistence Regeneration

Date: `2026-09-16`  
Status: `ACTIVE SHADOW RESEARCH CONTRACT`  
Production authority: `NONE`  
Market: `GOLD# ONLY`

## 1. Priority change

The previous Oracle-participation contract remains historical context, but the immediate work order is now:

```text
A. repair actual-tick execution semantics
B. rerun the exact bounded-m3 control
C. regenerate missing post-HEAD models / ledgers
D. only then test stage-aware policy changes
```

Do not continue model optimization while the actual-tick comparator has a known campaign-exit semantic defect.

## 2. Workstream A — persistent FAST-NHA exit intent

Implement and test:

```text
opposite FAST H4 finalized
-> EXIT_PENDING is earned
-> temporary market closure cannot erase it
-> retry until executable
-> later HA colors cannot cancel it
```

Structural stop remains higher-priority Child death.

Do not resurrect a structurally stopped Child.

## 3. Workstream B — unchanged bounded-m3 control rerun

Freeze:

```text
1,159 selected event definitions
1 / 3 unit payload
structural H1 SL
FAST w2/a0.25
timestamp fill-or-skip entry policy
first opposite FAST H4 campaign exit
```

Change only the rejected-exit persistence behavior.

Required report:

```text
fills
market-closed entry rejects
SL-already-touched rejects
pending-exit count
pending-exit delay distribution
actual PnL / PF
Balance DD
Equity DD
structural R
max single order
max concurrent units
LONG / SHORT
year split
right-tail concentration
```

Also reconcile every previous `FAST_NHA_EXIT_REJECT`.

## 4. Workstream C — entry execution comparators remain explicit

The current control is:

```text
market closed at exact entry timestamp
-> SKIP
```

Only after the corrected control rerun may a separate experiment test:

```text
FIRST_TRADABLE_TICK
```

Do not mix this into the control.

No fixed no-chase rule.

If the first tradable tick has already crossed the structural SL, reject fail-closed.

## 5. Workstream D — regenerate the k1 Danger Head

The session-recorded result:

```text
bounded m3 + extreme NHA-shock veto
PnL +15,013.69
PF 1.57811
~2,703.62 DD
+428.23R
```

is not implementation-ready because the exact model coefficients and veto-row ledger were not persisted.

Regeneration requirements:

```text
fixed causal feature definition
fixed training windows
saved coefficient vector
saved preprocessing
saved per-event score
saved prior-only percentile reference
saved veto decision
saved outcome / regret
```

Report both:

```text
selected-event precision
AND
economic delta
```

but do not promote a percentile.

## 6. Workstream E — preserve k1 role

Current hypothesis:

```text
k1
-> LOSS AVOIDANCE / RUN ADMISSION
```

Test compact danger features only.

Primary families:

```text
NHA-shock state
structural geometry
4h M15/M30/H1 body flow
persistence / same-opposite run asymmetry
opposing-wick morphology
lower-tail R state
```

Do not add every feature.

The objective is precision in the extreme bad tail, not broad discrimination.

## 7. Workstream F — regenerate k2 Persistence Head

Current hypothesis:

```text
k2
-> P(third same-color FAST H4 exists)
-> CONFIRM / STOP-ADDING context
```

Preserve the strong prior evidence:

```text
core state mean AUC ~0.795
LTF flow+persistence mean AUC ~0.776
M15 opposing-wick share around k2 ~0.754
```

Rebuild with saved coefficients and chronological evaluation.

Do not use k2 persistence as an automatic exit rule for already-profitable Children.

## 8. Workstream G — k3+ marginal economics

Once a campaign has survived the first two FAST opportunities, the research question changes.

Do not ask only:

```text
is this still early-third?
```

Ask:

```text
does one more Child add positive structural-R expectancy
without unacceptable incremental exposure?
```

Late non-Oracle participation in long runs can be profitable.

## 9. Workstream H — state-machine test

Only after D/E/F are reproducible:

```text
k1:
Opportunity + Danger
-> ABSTAIN / PARTICIPATE

k2:
Persistence
-> CONFIRM / STOP-ADDING

k3+:
marginal economics
-> ADD / HOLD / STOP-ADDING

FAST NHA:
EXIT
```

No fixed lot ladder becomes authority merely because it wins on consumed data.

## 10. Workstream I — right-tail and exposure audit

Every serious candidate must include:

```text
run count
run WR
median run PnL
p90 / p95
max run
top-1 contribution
top-5 contribution
lot-units
weighted position-hours
max single order
max concurrent units
Equity DD
structural R
```

V10 remains right-tail dependent.

## 11. Workstream J — direction and era stability

Required:

```text
2025 prior-only
2026 prior-2024/25 where applicable
LONG / SHORT
quarter / half-year
```

Do not create a 2026-specific fix.

## 12. Negative-result guardrail

Do not reflexively reopen:

- universal k1 down-sizing;
- pure k2/k3 delay;
- broad LTF trend gates;
- broad danger veto;
- automatic catch-up;
- k2 severe-loss veto;
- ERA_RISK minimum;
- fixed campaign cap;
- Oracle recall as sole objective;
- generic feature soup.

## 13. Promotion gate

No V10 production strategy exists.

Before promotion:

```text
fixed state semantics
reproducible model artifacts
corrected actual-tick execution
bounded exposure mapping
selection-stability controls
right-tail acceptance
forward-demo evidence
```

The immediate milestone is not promotion. It is a clean, reproducible actual-tick bounded-m3 control with correct campaign-exit semantics.
