# V9 Continuous Grammar Policy — Preliminary Branch Evidence

Date: `2026-09-13`  
Status: `PRELIMINARY BRANCH RESEARCH / REPRODUCTION REQUIRED ON CURRENT MAIN`  
Base main at review time: `19084062f136474469206eeeee20fadae5943c7f`

## Purpose

This file preserves the important evidence supplied from a separate research branch that motivated the unified-policy pivot.

These numbers are **not frozen authority** until they are reproduced from the current `main` research/runtime path.

## 1. 2024 existing-strategy proxy

Reported decomposition:

| subset | trades | total R | avg R | PF | max DD |
|---|---:|---:|---:|---:|---:|
| all resolved | 305 | +20.51 | +0.067 | 1.12 | -30.73 |
| COUNTER | 256 | +12.26 | +0.048 | 1.09 | -23.32 |
| WITH_PARENT all | 49 | +8.25 | +0.168 | 1.26 | -9.73 |
| WITH_PARENT FIRST | 34 | +17.05 | +0.501 | 1.81 | -6.21 |
| WITH_PARENT FRESH_REAUTH | 15 | -8.80 | -0.587 | 0.219 | not frozen here |

Research interpretation:

- lower-timeframe repeated reauthorization may fragment a larger H1 thesis;
- first-H1-participation quality deserves direct causal study;
- the result is still tail-dependent and does not prove a native-H1 strategy.

## 2. Preliminary state coverage

Reported valid H1 hours: `3,401`.

Reported nine state combinations:

| H4 phase | authority | H1 role | hours |
|---|---|---|---:|
| MIGRATION | STRONG | ALIGNED | 1,655 |
| LOCAL_INTERRUPT | STRONG | H1_INTERRUPT | 377 |
| MIGRATION | STRONG | H1_INTERRUPT | 297 |
| MIGRATION | WEAK | ALIGNED | 297 |
| NEUTRAL | NEUTRAL | N/A | 256 |
| LOCAL_INTERRUPT | WEAK | H1_INTERRUPT | 206 |
| LOCAL_INTERRUPT | STRONG | ALIGNED | 139 |
| LOCAL_INTERRUPT | WEAK | ALIGNED | 124 |
| MIGRATION | WEAK | H1_INTERRUPT | 50 |

## 3. Preliminary transition compression

Reported run transitions: `622`.

Reported primitive coverage: `615 / 622 = 98.9%`.

| transition primitive | count |
|---|---:|
| H1 interruption begins | 192 |
| H1 realigns | 159 |
| H4 migration resumes | 65 |
| H4 local interruption begins | 63 |
| enter neutral | 48 |
| leave neutral | 48 |
| authority strengthens | 29 |
| authority weakens | 11 |
| other | 7 |

## 4. Interruption authority-strength split

Reported H1 interruption-cycle outcome by H4 authority at interruption start:

```text
STRONG
142 cycles
119 H1 realign
23 H4 side change
83.8% realign

WEAK
44 cycles
24 H1 realign
20 H4 side change
54.5% realign
```

This is descriptive topology, not a mechanical trade rule.

## 5. Route / landmark density

Reported H1 interruption cycles: `186`.

```text
cycles with >=1 landmark event     163
cycles with >=3 landmark batches    74
cycles with >=5 landmark batches    38
median landmark batches              2
mean landmark batches              2.86
max landmark batches                 18
```

Reported resolution split:

```text
same-Parent realign cycles   143   median 2   mean 2.35 batches
Parent side-change cycles     43   median 4   mean 4.56 batches
```

This motivates route-stage research inside one H1 auction.

## 6. Meaningful event coverage

Reported Atlas semantic events:

```text
total semantic events        2,487
unique event batches         1,828
POI_CLUSTER_TOUCH            1,128
LIQUIDITY_DELIVERY             651
H4_STATE_START                 336
H1_INTERRUPT_START             186
H1_INTERRUPT_RESOLUTION        186
```

Reported active trading dates: `171`.

```text
mean event batches/day       10.7
median                         11
90% <=                         15
max                            18
```

The `244 / 1,828` comparison between first strategy authorizations and semantic event batches is evidence of narrow strategy extraction only; it must **not** be interpreted as 86.7% missed profitable opportunities.

## 7. Candidate policy interpretation

The branch research proposed:

```text
MARKET STATE
+
TRANSITION
+
ROUTE / LANDMARK STAGE
+
POSITION STATE
-> ACTION
```

Candidate actions:

```text
WAIT
ARM_PARENT
ARM_COUNTER
ENTER
HOLD
EXIT
REMAP
RESET
```

This evidence file preserves the research hypothesis. Current authority is the separate next-research contract, which requires reproduction and causal decision-sufficiency testing before any new trade rule is frozen.
