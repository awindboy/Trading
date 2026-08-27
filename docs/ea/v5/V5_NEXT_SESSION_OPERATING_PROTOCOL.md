# V5 — Next Session Operating Protocol

Status: `MANDATORY HANDOFF`
Date: `2026-08-27`

This file exists so a new chat can continue the current research method without relying on conversational memory.

## Startup

1. Check GitHub `main` HEAD.
2. Read root `AGENTS.md`.
3. Read root `docs/ea/HANDOFF.md`.
4. Read:
   - `docs/ea/v5/AGENTS_V5.md`
   - `docs/ea/v5/HANDOFF_V5.md`
   - `docs/ea/v5/RESEARCH_STATE_V5.md`
   - `docs/ea/v5/V5_030A_FIRST_CROSS_240M_DEVELOPMENT_RESULTS.md`
   - `docs/ea/v5/V5_034A_FIRST_CROSS_240M_VALIDATION_CANDIDATE_FREEZE.md`
   - `docs/ea/v5/V5_034A_EXTERNAL_VALIDATION_CONTRACT.md`
   - `docs/ea/v5/V5_RECURSIVE_FALSIFICATION_PROTOCOL.md`
   - `docs/ea/v5/BACKLOG_V5.md`.

GitHub wins over chat memory.

## Current authority

```text
active candidate:
V5_FIRST_CROSS_240M_HALF_EMA_RUNNER

state:
DEVELOPMENT PASS
FROZEN FOR EXTERNAL VALIDATION
NOT PRODUCTION AUTHORITY
```

## Prohibited next-session behavior

Do not begin by:
- searching another successful trader setup;
- adding a filter to V5-030A;
- rerunning the development grid for a better timeframe;
- removing USDJPY because it was negative;
- using GOLD# 2022 as validation;
- opening GOLD# 2021;
- restarting V4 AI as a rescue.

The next empirical task is external validation.

## User reporting preference

The user explicitly asked not to receive a message for every failed intermediate hypothesis.

During long research:
- work through negative controls internally;
- provide occasional progress only when needed;
- report when a meaningful phase result exists, a user action is required, or a frozen decision changes.

This does not relax documentation. Every material failure/decision must still be recorded in GitHub before the next phase.

## Recursive self-questioning

Before every interpretation ask:

```text
What if the opposite is true?
Can a simpler confounder explain this?
Did V1-V4/V5 already fail in the same way?
What is the placebo?
Was all information causal?
Did confirmation consume payoff?
What exact outcome kills the hypothesis?
```

Do not let the latest narrative become project truth merely because it is coherent.

## If external validation data are available

1. verify file identities/coverage/point/spread;
2. create local data map from the template;
3. run `tools/run_v5_034_external_validation.ps1`;
4. inspect result summary before any visualization/story;
5. apply the frozen V5-034A gate;
6. record PASS / FAIL / INCONCLUSIVE;
7. do not retune.

## If external validation data are not available

Only:
- prepare/export the four required raw M1 files;
- improve replay reproducibility without changing semantics;
- inspect source literature for documentation purposes.

Do not consume more development outcomes.

## If V5-034A FAILS

Return to the success-first corpus at the **mechanism** level, not the threshold level.

A new phase must begin with:
- successful-trader/source evidence;
- a different market mechanism;
- an explicit explanation of why it is not V5-030A rescue;
- pre-registration before outcomes.

## If V5-034A PASSES

Do not celebrate as production-ready.

Next:
- GOLD# 2021 temporal confirmation;
- isolated MT5 implementation;
- real-tick/full-cost execution validation;
- portfolio/exposure research only after single-trade semantics survive.
