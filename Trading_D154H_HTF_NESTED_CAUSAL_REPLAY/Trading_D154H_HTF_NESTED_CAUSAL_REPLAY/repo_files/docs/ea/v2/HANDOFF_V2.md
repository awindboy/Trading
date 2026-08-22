# V2 Development Handoff

Last updated: 2026-08-22  
Repository base before D-154H package: `0c2561619b70eff6deafa90cf9a79730de2e5848`  
Current committed EA: `2.07R0L7 / V2_D154G_HTF_ROOT_BIRTH_LINEAGE_AUDIT`  
Target research build: `2.08R0L8 / V2_D154H_HTF_NESTED_CAUSAL_REPLAY`  
Current phase: **D-154G COMPLETE / NO HTF FILTER PROMOTED / D-154H NESTED CAUSAL REPLAY NEXT**  
V1: **FROZEN HISTORICAL CONTROL**  
2021: **KEEP UNTOUCHED**

## Startup order

1. Check latest GitHub commit.
2. Read root `AGENTS.md`.
3. Read `docs/ea/v2/AGENTS_V2.md`.
4. Read root `docs/ea/HANDOFF.md`.
5. Read this file.
6. Read `docs/ea/v2/D154G_HTF_ROOT_BIRTH_LINEAGE_RESULTS.md`.
7. Read `docs/ea/v2/D154H_HTF_NESTED_CAUSAL_REPLAY.md`.
8. Read `RESEARCH_STATE_V2.md` and `BACKLOG_V2.md`.

GitHub remains the Single Source of Truth.

## Strategy authority

Unchanged: EXTERNAL_CONTINUATION only, BASELINE_NO_REGIME_GATE, ROOT_OB_DISTAL_20, LAST_OPPOSITE_OB + FVG_ORIGIN_OB, PD reference only, same-entry Root merge, same-direction add-ons, no look-ahead.

D-154H is shadow-only.

## Entry-research control

```text
post-+1R research reference = V3E BANK_2R_LOCK_ONE (mode 9)
EM = OFF
D151 = ON
```

## D-154G result

- `HAS_PRIOR_SAME_TF_OWNER` had zero coverage in all 457 observed fills across discovery + validation.
- GOLD23 same-owner pre-entry BOS refresh weakness did not generalize; GOLD24 and CADJPY25 reversed it.
- Simple static H1/M30 alignment did not generalize.
- No Root-age/source-TF/direction/market rescue is allowed.
- No strategy change.

## D-154H question

Instead of another scalar or boolean HTF filter, preserve the ordered H1/M30 path that led to each Fill.

D-154H logs H1/M30 INITIAL_BOS/BOS/PROTECTED_BREAK plus sequence-numbered stage anchors at PLAN, Root contact, Sweep, CHOCH, Pending and Fill. Actual Fill remains the outcome unit even when multiple Roots merge.

D-154H discovery does not authorize a gate. Any candidate sequence family discovered on GOLD23 must be defined before a later independent validation phase.

## Required next steps

```text
1. Apply D-154H on exact committed D-154G state.
2. Compile 0 errors.
3. Refresh tester preset and confirm InpV2D154HHTFNestedReplayAudit.
4. Run GOLD23 Q1 OFF/ON parity and comparator.
5. Run GOLD23 clean discovery through 2023-12-21.
6. Send discovery ZIP for sequence analysis.
```
