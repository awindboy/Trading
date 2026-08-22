# V2 Development Handoff

Last updated: 2026-08-22  
Repository base before D-154G package: `9808edb2a7c816e5d6630a7d79e35bf525bbe549`  
Current committed EA: `2.06R0L6 / V2_D154F_CAUSAL_LINEAGE_AUDIT`  
Target research build: `2.07R0L7 / V2_D154G_HTF_ROOT_BIRTH_LINEAGE_AUDIT`  
Current phase: **D-154F COMPLETE / LOCAL-M1 HYPOTHESES NOT PROMOTED / D-154G HTF ROOT BIRTH LINEAGE NEXT**  
V1: **FROZEN HISTORICAL CONTROL**  
2021: **KEEP UNTOUCHED**

## Startup order

1. Check latest GitHub commit.
2. Read root `AGENTS.md`.
3. Read `docs/ea/v2/AGENTS_V2.md`.
4. Read root `docs/ea/HANDOFF.md`.
5. Read this file.
6. Read `docs/ea/v2/D154F_CAUSAL_LINEAGE_RESULTS.md`.
7. Read `docs/ea/v2/D154G_HTF_ROOT_BIRTH_LINEAGE_AUDIT.md`.
8. Read `docs/ea/v2/RESEARCH_STATE_V2.md` and `BACKLOG_V2.md`.
9. Read D148/D151/D152 evidence only as needed.

GitHub remains the Single Source of Truth.

## Strategy authority

Unchanged:

```text
EXTERNAL_CONTINUATION only
BASELINE_NO_REGIME_GATE
ROOT_OB_DISTAL_20
LAST_OPPOSITE_OB + FVG_ORIGIN_OB
PD reference only
same-entry Root merge
same-direction hedging add-ons
no look-ahead
```

D-154G is shadow-only and has no strategy authority.

## Post-+1R reference / EM

For current Entry-survival research runs:

```text
SP/exit research reference = V3E BANK_2R_LOCK_ONE (mode 9)
EM = OFF
```

V3E is still provisional and is not baseline promotion.

## D-154F completed result

Read `D154F_CAUSAL_LINEAGE_RESULTS.md`.

Key decisions:

- `DIRECT_FROZEN_BREAK` not promoted.
- GOLD23 `TRANSITION at sweep` discovery did not generalize and is rejected as a veto.
- BTC25 and CADJPY25 reversed the GOLD23 relation.
- Do not tune local M1 timing/state thresholds to rescue D-154F.
- M1 confirmation research pauses while the project moves upstream.

## Current causal question

The current code can authorize a Root because its direction matches the current H1/M30 continuation map and its zone lies inside the current map range, even though the Root does not store the H1/M30 owner context that existed when it was born.

D-154G asks whether actual fills are weaker when one or more same-entry contributor Roots were born under a **different mature owner on the same timeframe later frozen into that contributor's PLAN**.

`M30 -> later H1 promotion` is explicitly separated from stale prior-owner lineage.

## Required validation order

```text
1. Apply D-154G package on exact D-154F committed EA state.
2. MetaEditor compile = 0 errors.
3. Refresh Strategy Tester preset; confirm InpV2D154GHTFRootLineageAudit exists.
4. GOLD23 Q1 D154G OFF/ON parity.
5. compare_d154g_parity.py => PASS.
6. GOLD23 clean discovery through 2023-12-21.
7. Analyze frozen stale-owner definition.
8. Only if discovery warrants it, run pre-registered GOLD24/GOLD25/BTC25/SILVER25/CADJPY25 validation.
```

Do not run validation early. Do not alter the stale definition after seeing discovery.

## If D-154G validates

Only then consider one controlled strategy variant that requires current-episode Root ownership. The exact rule must be derived from the validated lineage class, not from Root age or a fitted score.

## If D-154G fails

Do not tune Root age, source TF, direction or market exceptions. Move to the next HTF premise representation question, such as nested H1/M30 continuation/correction state, while preserving the baseline control.
