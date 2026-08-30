# V8 Research State

Status: `ACTIVE / V8-A FROZEN + V8-B DEVELOPMENT CANDIDATE`
Date: `2026-08-31`
Current phase: `V8-B1 CONDITIONAL DIRECTION PROBABILITY`
Production authority: `NONE`
EA authority: `NONE`
Direction trade authority: `NONE`

## Phase map

### V8-000 through V8-004
`COMPLETE`

See `V8_RESEARCH_JOURNEY.md` for the full sequence from representation reset through failed unconditional direction research and successful movement-intensity separation.

### V8-A — movement probability
`FROZEN / SHADOW IMPLEMENTATION`

V8-A remains the existing movement-intensity branch.

Target:

```text
P(any +/-10.0 move within H), H in {15m,30m,60m}
```

Do not tune V8-A from V8-B results.

### V8-B0 — direct/gated movement-probability-as-direction-feature hypothesis
`COMPLETE / FALSIFIED`

Adding `p15/p30/p60` directly to the conditional side model did not improve side AUC. Continuous interaction/gating models were also worse or less stable than the signed causal core.

### V8-B1 — same-horizon conditional side decomposition
`POSITIVE OPEN-DEVELOPMENT EVIDENCE`

Definition:

```text
q_H = P(UP first | a +/-10.0 move occurs within H, causal context)
UP_H   = p_H*q_H
DOWN_H = p_H*(1-q_H)
NO_H   = 1-p_H
```

Conditional side AUC, all prior movers:

| Horizon | 2024 | 2025 | 2026 |
|---|---:|---:|---:|
| 15m | 0.846 | 0.866 | 0.838 |
| 30m | 0.895 | 0.869 | 0.823 |
| 60m | 0.863 | 0.842 | 0.795 |

Non-overlap evaluation remains strong and week-block bootstrap intervals remain well above 0.5.

### Event suitability

M5 SMA20 / upper-BB / lower-BB events retain strong V8-B information.

H1 Double-B does not. Direction output remains unauthorized for Double-B.

### V8-B2 — MT5 shadow implementation
`PENDING`

Requirements:

- freeze exact signed-feature equations and coefficients;
- no change to V8-A;
- output conditional and joint probabilities separately;
- Python/MQL parity;
- no trade actions;
- Double-B direction blank.

### V8-006 — untouched GOLD# 2021
`LOCKED`

Do not open until V8-B2 implementation/protocol freeze if V8-B is promoted to untouched validation.

## Strongest current interpretation

The prior conclusion `GOLD past context -> future sign weak` was too broad.

The refined finding is:

```text
unconditional / eventually-resolved sign: weak and unstable
near-term side conditional on a real expansion: materially predictable
movement intensity itself: strongly predictable
```

The side signal is dominated by signed M15/H1 progression and is weaker in the most extreme movement-intensity states.

## Restrictions

Do not:

- retrofit V8-A to improve V8-B;
- report q_H as unconditional LONG probability;
- report p_H as directional confidence;
- give Double-B a V8-B direction output;
- use retrospective joint-probability tails as a trade threshold;
- open GOLD# 2021 before implementation/protocol freeze;
- treat overlapping event hits as independent proof.

## Required current documents

- `V8_B_DIRECTION_PROBABILITY_RESULTS.md`
- `V8_RESEARCH_JOURNEY.md`
- `HANDOFF_V8.md`
- `DECISIONS_V8.md`
- `V8_005_MOVEMENT_PROBABILITY_INDICATOR.md`
