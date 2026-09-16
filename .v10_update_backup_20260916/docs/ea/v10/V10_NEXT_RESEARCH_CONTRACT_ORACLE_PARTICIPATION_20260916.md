# V10 Next Research Contract — Oracle Participation Replication

Date: `2026-09-16`
Status: `ACTIVE SHADOW RESEARCH CONTRACT`
Production authority: `NONE`
Market: `GOLD# ONLY`

## 1. Primary objective

The next V10 objective is:

> Reduce false-positive participation while preserving high recall of the future early-run Oracle and the right tail of long trends.

Do not optimize a new arbitrary indicator soup.

## 2. Frozen research comparators for the next stage

Current FAST execution universe:

```text
ALL1
2,489 eligible opportunities
PnL +10,007.27
PF 1.368
DD 2,034.28
+253.72R
```

Future-only answer sheet:

```text
TRUE FAST EARLY THIRD
567 entries
PnL +23,344.73
PF 15.157
DD 148.81
+733.18R
```

Current bounded diagnostic reference:

```text
P_RUNWAY(3x) * P_WIN * P_STD_SUPPORT
prior quartile 0/0/1/3 map

PnL +14,827.57
PF 1.553
DD 2,638.04
+388.88R

Oracle recall 80.4%
Oracle precision 39.3%
```

No element above is production authority.

## 3. Workstream A — false-positive decomposition

For every selected non-Oracle bar, reconstruct causally:

```text
FAST run state
STD support state
SLOW state
Grammar state
H1 structural risk
M15/M30/H1 delivery
runway probabilities
P_WIN
score transition
Child outcome
run-level regret
```

Rank false positives by economic regret, not count.

Target question:

> Which false positives are harmless profitable continuation and which are destructive late/chop exposure?

## 4. Workstream B — FRONT-LOAD vs CONTINUATION state

Treat:

```text
TOP_NEW
```

and

```text
TOP_PERSIST
```

as semantically different.

Test a state machine:

```text
FRONT-LOAD
-> initial exposure acquisition

CONTINUATION
-> optional additional exposure only when economic quality remains healthy

STOP-ADDING
-> no new Child

FAST NHA
-> campaign exit
```

Do not assign fixed lot sizes before the state semantics are stable.

## 5. Workstream C — expected Oracle exposure

Continue the cumulative-target lane:

```text
expected Oracle count
= state-conditioned probability of L>=3,6,9,12,15...
```

Questions:

- Does route-weighted fitting improve 2026 stability?
- Should cumulative target be based on expected count, lower quantile, or bounded target class?
- Can cumulative target reduce concurrent exposure without losing Oracle recall?
- How much is gained by front-loading when the score first enters a high state?

Do not create a fixed “every three bars” ladder.

## 6. Workstream D — runway semantics

Continue runway labels only as a family:

```text
L >= 2k
L >= 3k
L >= 4k
...
```

Do not select one `m` from pooled PnL and call it authority.

Study:

- false-positive identity by `m`;
- right-tail capture;
- DD / concurrent exposure;
- whether a small mixture of adjacent runway probabilities is more stable than a single `m`.

## 7. Workstream E — multi-timeframe HA

Keep the current role hypothesis:

```text
H4 FAST -> execution
H4 STD  -> maturity / support
H4 SLOW -> broad regime
H1 STD  -> meso delivery
M30 FAST / M15 FAST -> internal H4 delivery
```

Required tests:

- fixed compact feature families;
- no per-year feature-family switching;
- interaction with TOP_NEW / TOP_PERSIST;
- whether M15/M30 improves false-positive rejection rather than only AUC.

Do not add every LTF coordinate.

## 8. Workstream F — standard-HA support

The current directional support transform is:

```text
if STD direction == FAST direction:
    support = P_STD_EARLY
else:
    support = 1 - P_STD_EARLY
```

Test whether the value comes from:

- STD direction agreement;
- STD early probability;
- the interaction of both;
- STD score transition.

Do not hard-code a support threshold yet.

## 9. Workstream G — economic-quality head

`P_WIN` alone has modest AUC but improves the Oracle-likeness score when multiplied with it.

Investigate:

- risk-normalized Child return as a continuous target;
- loss-tail / stop probability rather than simple win label;
- positive expected structural-R;
- whether current economic head is mostly filtering large losers.

The economic head must remain causal.

## 10. Workstream H — robustness

Every serious candidate must report:

```text
2025 prior-2024 result
2026 prior-2024/25 result
pooled result
route bootstrap
direction split
right-tail concentration
lot-units
position-hours
max single order
max concurrent units
raw PnL / PF / DD
structural R
Oracle recall / precision
```

AUC is not sufficient.

## 11. Workstream I — execution fidelity

Before promotion:

- rebuild V10 FAST entries and H1 stops on actual ticks;
- resolve same-minute M1 ambiguity;
- confirm Bid/Ask execution;
- compare M1 first-touch screening to tick-native ledger;
- keep stopped Children dead;
- record every collision ordering explicitly.

## 12. Forward gate

No V10 strategy can be promoted until:

- the state representation is fixed;
- feature-family selection is fixed;
- exposure mapping is bounded and fixed;
- actual-tick replay is complete;
- right-tail dependence is accepted / bounded;
- forward-demo evidence exists.

Until then, V10 remains research only.
