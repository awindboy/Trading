# V12 Phase-1B H4-M5 journey and V10 overlay result

Date: `2026-09-23`

Status: `REPRODUCIBLE CONSUMED-DEVELOPMENT DIAGNOSTIC / NO TRADE OR SIZING AUTHORITY`

Contract: `v12-phase1b-h4m5-journey-v1.1`

## Scope and integrity

This phase tested an empirical V12 H4->M5 CRT extension. It is not attributed
to Romeo. Verified GOLD# raw M1 was streamed chronologically through
`2026-09-18 23:57`; zero later price rows were parsed. Two independent builds
produced byte-identical decision, outcome, scorecard, diagnostic, and render
files.

The pack contains:

- `7,287` exhaustive consecutive-H4 C1/C2 decisions;
- `4,819` causal activations and `2,649` canonical journeys;
- `17,610` completed-period one-use key-level objects;
- `2,234` completed FAST-HA direction changes;
- all `1,649` frozen selected R7G Children without changing an action or size.

The V10 invariants remain `3,881` funded units, `486` stopped units, and
`+741.010865R`.

## Journey result

The state machine covered `88.20%` of completed H4 observations and had an
eight-hour median duration. `1,437` journeys ended by completed-H4 structural
failure and `1,211` by opposite activation. Among targets still ahead at
activation, C1 midpoint attainment was `70.88%` and opposite-edge attainment
was `44.67%`.

This is useful lifecycle coverage but not a standalone entry edge. The median
signed H4 close-path efficiency was `-0.3081`, and the state is active too often
to serve as a selective admission gate by itself.

## Frozen V10 Child overlay

| Causal relation | Children | Stop rate | Stopped units / 100 funded | R / 100 funded | Weighted R |
|---|---:|---:|---:|---:|---:|
| aligned active journey | 1,184 | 11.06% | 10.43 | 17.38 | +498.40R |
| no active journey | 150 | 16.67% | 13.64 | 14.21 | +46.89R |
| opposed active journey | 315 | 24.13% | 20.79 | 28.66 | +195.72R |

Alignment separates stop burden: the opposed group has about twice the stopped
exposure per funded unit. The ordering persists in 2024, 2025, and 2026.
However, the opposed group also carries `+195.72R` and `+296.12R` of positive
>=5R units. Therefore `OPPOSED_ACTIVE_JOURNEY` is not a valid veto.

Inside aligned journeys, the first selected Child had `14.88` stopped units per
100 funded; later aligned Children had `5.82`. The later group retained
`+219.63R` on 1,410 funded units. Its lower stop burden held in every selected
year, but its 2024 R was negative. This is conviction/capacity evidence, not an
automatic size-release rule.

## FAST transition result

The clearest finding concerns the new-direction k1 after a completed FAST flip:

| Causal meaning at flip | Linked k1 | Stop rate | Net R |
|---|---:|---:|---:|
| opposite CRT journey authorized | 1,294 | 26.12% | +114.38R |
| all other states | 807 | 36.93% | +35.42R |
| old journey still active, pooled | 455 | 42.86% | +14.75R |

The authorized stop rate was lower in every consumed year:

| Year | Authorized | Not authorized |
|---|---:|---:|
| 2022 | 27.35% | 40.44% |
| 2023 | 32.65% | 38.46% |
| 2024 | 28.28% | 32.95% |
| 2025 | 20.68% | 33.94% |
| 2026 | 18.75% | 39.42% |

Descriptively, the authorized population is `61.6%` of linked k1 attempts,
contains `53.1%` of their stops, and retains `76.4%` of their net R. This is a
meaningful stop-risk partition, but not a validated policy: the excluded group
is still net positive, and all thresholds and meanings were observed on consumed
history.

External key arrival alone did not solve the transition. A flip while the old
journey remained active had a `40.91%` linked-k1 stop rate after a same-direction
arrival and `46.94%` without one; annual R and stop behavior were not stable
enough to promote arrival as a rule.

## Decision

Phase 1B succeeds as a structural reassembly diagnostic and fails as a direct
entry filter or profit oracle.

The retained V12 mechanism is:

```text
FAST flip / NHA
-> interruption is observed
-> opposite CRT journey present: independent opposite direction is authorized
-> old CRT journey remains: classify as counterflow, not automatic reversal
-> old journey failed but no opposite journey: remain neutral
-> later same-direction CRT activation may create new authorization
```

This directly addresses the V10 ambiguity between Child interruption and
opposite-direction authorization. It does not yet say to block, delay, or resize
an order.

## Next research boundary

The next shadow must keep candidate creation unchanged and test the transition
meaning conditionally:

1. FAST/STD/SLOW disagreement and Wave coordinates inside the five frozen flip
   states, not as global gates;
2. first versus later aligned Child as a conviction observation, not a fixed
   capital ladder;
3. separate competing outcomes for immediate new-direction stop, later repair,
   and right-tail continuation;
4. a future-frozen `authorize / neutral bridge / later reauthorize` lifecycle
   that never treats non-authorization as permanent rejection.

No consumed-data threshold, V10 veto, sizing map, EA, MQL5 parity, actual-tick
economics, or independent future validation is granted by this result. GOLD#
2021 remains sealed.
