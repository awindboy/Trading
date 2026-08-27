# V5 Development Handoff

Last updated: `2026-08-27`
Current phase: `V5-037A GOLD REAL-YIELD DIRECTIONAL-DELIVERY MECHANISM AUDIT`
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
8. `DECISIONS_V5_APPEND_D183_D184.md`;
9. `V5_036A_CROSS_ARCH_CONTINUATION_PORTABILITY_RESULTS.md`;
10. `V5_037A_SOURCE_REVIEW_AND_LINEAGE_SCREEN.md`;
11. `V5_037A_GOLD_REAL_YIELD_DIRECTIONAL_DELIVERY_CONTRACT.md`;
12. `V5_035A_PAYOFF_CAPACITY_AUDIT_RESULTS.md`;
13. `V5_026_TO_V5_033_FIRST_CROSS_SYNTHESIS.md`;
14. `V5_SOURCE_LEDGER.md`;
15. `BACKLOG_V5.md`.

GitHub wins over chat memory.

## Final economics — D-180

```text
realized positive-trade rate >= 50%
average positive NET R       >= 2R
cost-adjusted EV             > 0
```

The 2R requirement is a result criterion, not a fixed TP authorization.

## First Cross final disposition

V5-030A remains preserved history:

```text
WR 53.94%
avg positive net R 1.197R
EV +0.148R
```

Classification:

```text
OLD-GATE DEVELOPMENT PASS
NEW-GATE FINAL ECONOMICS FAIL
PAYOFF-RESCUE CLOSED
```

Do not continue V5-034A promotion validation and do not retune First Cross.

## V5-036A completed result

Stage 0:
- exact D-145/D-146 M30 protected->external progress is portable as a causal measurement;
- it is derived from global M30 price-structure state, not Root/FVG/scenario identity.

Stage 1:
- inherited prediction was `runner progress < exhaust progress`;
- pooled First Cross result reversed: runner median `1.0074`, exhaust `0.9649`;
- 2/4 markets support;
- only 2023 supports, while 2024 and 2025 reverse;
- LONG and SHORT both reverse;
- 3/9 comparable cells support.

Classification:

```text
PORTABLE OBSERVABLE
BUT
CROSS-ARCHITECTURE EDGE TRANSFER FAIL
```

Do not create a progress threshold, market veto, direction veto or management rule from V5-036A.

## Why V5-037A exists

V5-036A ended the First Cross rescue branch.

The next branch must be materially different from already-consumed chart-only setup families.

V5-037A tests an external economic state before constructing any Entry:

```text
causally known US 10y TIPS real-yield change
-> next complete GOLD broker-day directional delivery
```

This is not a claim that the H.15 publication causes the move. `DFII10` is used only as a slow, point-in-time external-state measurement.

## Immediate next task

Only:

```text
Acquire/verify point-in-time DFII10 release history,
freeze release-date identity,
and run V5-037A Stage 1 on GOLD# 2023 only.
```

Before outcomes:
- use ALFRED release-dated/vintage data or defensible H.15 release archive;
- do not treat FRED observation date as same-day availability;
- do not open GOLD 2024/2025;
- do not add USD or a second macro variable.

If Stage 1 fails any frozen sign/order gate:
- close V5-037A;
- do not rescue it with magnitude/session/month/direction filters.

If Stage 1 passes:
- freeze the mechanism;
- then validate unchanged on GOLD# 2024 and 2025 before any Entry research.

## Hard stops

- do not reopen First Cross payoff rescue;
- do not reopen V5-034A promotion validation;
- do not tune partial/BE/EMA/slow exits;
- do not import V3 rules as V5 authority;
- do not use same-day H.15/H.10 data before actual publication;
- do not inspect GOLD# 2021;
- do not modify production EA.
