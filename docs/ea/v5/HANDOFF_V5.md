# V5 Development Handoff

Last updated: `2026-08-27`
Current phase: `V5-036A CROSS-ARCHITECTURE CONTINUATION-STATE PORTABILITY`
Current promoted candidate: `NONE`
Production authority: `NONE`

## Startup — mandatory

Read in order:

1. latest GitHub HEAD;
2. root `AGENTS.md`;
3. root `docs/ea/HANDOFF.md`;
4. `AGENTS_V5.md`;
5. this file;
6. `RESEARCH_STATE_V5.md`;
7. `DECISIONS_V5_APPEND_D180_D182.md`;
8. `V5_035A_PAYOFF_CAPACITY_AUDIT_RESULTS.md`;
9. `V5_035B_STRUCTURAL_LOCK_AVAILABILITY_RESULTS.md`;
10. `V5_035C_POST1_CONTINUATION_STATE_RESULTS.md`;
11. `V5_036A_CROSS_ARCH_CONTINUATION_PORTABILITY_CONTRACT.md`;
12. `docs/ea/D145_RUNNER_GENERALIZATION_RESULTS.md`;
13. `docs/ea/D146_CONTINUATION_STATE_AUDIT.md`;
14. `V5_026_TO_V5_033_FIRST_CROSS_SYNTHESIS.md`;
15. `BACKLOG_V5.md`.

GitHub wins over chat memory.

## New final economics

```text
WR >= 50%
average positive NET R >= 2R
cost-adjusted EV > 0
```

The 2R requirement is a result criterion, not a fixed TP authorization.

## First Cross reclassification

V5-030A:

```text
WR 53.94%
avg positive net R 1.197R
EV +0.148R
```

It remains an important old-gate development PASS but is a new-gate FINAL ECONOMICS FAIL.

Do not continue V5-034A external promotion work.

## What V5-035 established

### V5-035A

- raw structural-regime >=2R MFE: 28.85%;
- among clear +1R survivors, 45.29% reached >=2R before current runner end;
- current positive trades realize >=2R net only 10.96%.

The current partial-fraction family cannot solve the new target:
- best avg positive at WR >=50% ~= 1.515R;
- best WR while avg positive >=2R ~= 39.66%.

### V5-035B

A new favorable 240m pivot stop was available in only 25% of current partial-BE trades before BE.
Median maximum available lock in those cases was ~0.765R.

### V5-035C

At +1R:
- slow regime alive was strong pooled but nearly absent as a discriminator for SHORT;
- fast alignment and EMA20 side were weak/unstable.

No rule is authorized.

## Why V5-036A exists

D-145 found that among +1R survivors, lower M30 protected->external maturity was associated with +2R continuation in:
- 6/6 market-year aggregates;
- 11/11 comparable market-year x direction cells.

V3's Entry survival was weak; First Cross survival is better.

Do NOT combine strategies.

First determine whether the D-145 state is genuinely Entry-independent and portable.

## Immediate next task

Read the exact D-145/D-146 implementation and answer:

```text
Can one_r_m30_range_progress be defined for First Cross
without importing Root/FVG scenario-specific state?
```

If NO:
- classify NONPORTABLE;
- close First Cross payoff-rescue work;
- return to payoff-first success-first discovery.

If YES:
- freeze exact causal definition;
- run shadow-only transfer falsification;
- no threshold;
- no management change.

## Hard stops

- do not reopen V5-034A promotion validation;
- do not tune First Cross partial fraction;
- do not add a direction veto;
- do not turn slow-alive into a rule;
- do not approximate D-145 M30 state if scenario-specific;
- do not inspect GOLD# 2021;
- do not modify production EA.
