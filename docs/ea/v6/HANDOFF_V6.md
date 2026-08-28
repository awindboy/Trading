# V6 Development Handoff

Last updated: `2026-08-28`
Current phase: `V6-001A SAME-CAPACITY CROSS-MARKET CONTEXT INFORMATION AUDIT`
Current promoted candidate: `NONE`
Production authority: `NONE`

## Mandatory startup

1. Check latest GitHub HEAD.
2. Read root `AGENTS.md`.
3. Read root `docs/ea/HANDOFF.md`.
4. Read `AGENTS_V6.md`.
5. Read this file.
6. Read `RESEARCH_STATE_V6.md`.
7. Read `V6_000_RESEARCH_CONTRACT.md`.
8. Read `V6_FAILURE_MAP_V3_V4_V5.md`.
9. Read `V6_001A_CONTEXT_INFORMATION_AUDIT.md`.
10. Read `BACKLOG_V6.md`.
11. Read `../v5/V5_FINAL_SYNTHESIS.md`.
12. Inspect exact V3/V4 code and any recovered late-V5 scratch implementation before execution.

GitHub wins over chat memory.

## Why V6 exists

User-level intended direction:

> use modern technology/research to solve the limitation exposed by V3 more intelligently.

Do NOT reinterpret this as:
- abandon GOLD;
- enumerate macro variables;
- copy another trader's market;
- rerun V4 with a bigger model.

## Non-negotiable inherited facts

### V3

V3's encouraging GOLD 2023-2025 behavior did not survive GOLD 2022 validation / broader-market checks.
V6 must solve or explicitly explain this generalization problem.

### V4

Actual model-learning attempts did not produce meaningful learned signal.
V6 must establish learnability/information before deep-model escalation.

### V5

Read `V5_FINAL_SYNTHESIS.md`.
First Cross is closed.
The late V5 AI/context scratch is the transition point, not strategy authority.

## Exact next task

Finish the unresolved capacity confound:

```text
Arm A: GOLD-only
Arm B: GOLD x3 exact duplicate placebo (30ch, no new information)
Arm C: GOLD + XAUEUR + USDJPY (30ch, real context)
```

Primary target:

```text
W_CONTINUE vs L_CONTINUE
```

Chronology:

```text
train 2023 -> eval 2024
train 2023-2024 -> eval 2025
```

Before outcome:
- recover/audit the exact late-V5 context builder/probe if available;
- record SHA/config;
- construct `GOLDx3` by exact block duplication, not by adding new GOLD features;
- use identical model capacity and seeds for B/C.

Decision:

```text
C beats B in both years -> incremental context remains alive
otherwise               -> close this context claim
```

Do not select best TF.
Do not tune context composition.

## Known late-V5 scratch numbers — descriptive only

Recovered robust-endpoint diagnostics:

```text
                         GOLD only   +XAUEUR+USDJPY
2024 AUC                    0.486          0.514
2025 AUC                    0.645          0.709
```

Known ordinal diagnostics:

```text
                         GOLD only   +XAUEUR+USDJPY
2024 rho                   -0.034         +0.030
2025 rho                   +0.084         +0.191
```

These are NOT final V6 evidence because the same-capacity placebo was not run.

## After V6-001A

If context information survives controls:
- freeze result;
- open V6-001B to diagnose residual concept drift;
- compare static context vs strictly causal limited adaptation;
- adaptation design must be preregistered before results.

If context information fails:
- do not shop for alternative context markets;
- reconsider event formulation / observable state;
- document negative result.

## Data/validation restrictions

- 2023/2024/2025 are consumed development environments for this research question.
- GOLD 2022 is consumed by V3 and may only be a later frozen falsifier.
- GOLD# 2021 stays untouched.
- no production EA modification.
