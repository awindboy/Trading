# EA Development Handoff

Status: `ACTIVE V7 ROUTER`
Date: `2026-08-30`
Expected base HEAD for this transition package: `102791741620ca6cffe061f077d83116a1e46c09`
Active generation: `V7`
Current phase: `V7-001 DOUBLE-B / CONTEXT / KTR DISCRETIONARY RESEARCH`
Production authority: `NONE`
Untouched reserve: `GOLD 2021`

## Startup order

1. Check latest GitHub HEAD.
2. Read root `AGENTS.md`.
3. Read this file.
4. Read `docs/ea/WORKFLOW_AND_ZIP_HANDOFF.md`.
5. Read `docs/ea/v7/AGENTS_V7.md`.
6. Read `docs/ea/v7/HANDOFF_V7.md`.
7. Read `docs/ea/v7/RESEARCH_STATE_V7.md`.
8. Read `docs/ea/v7/V7_000_RESEARCH_CONTRACT.md`.
9. Read `docs/ea/v7/V7_001_KIMJIKSEON_METHOD_SPEC.md`.
10. Read `docs/ea/v7/V7_002_OUTCOME_REVERSE_ENGINEERING_RESULTS.md`.
11. Read `docs/ea/v7/DECISIONS_V7.md` and `BACKLOG_V7.md`.
12. Inspect exact code/data/ledger before changing semantics.

GitHub is the Single Source of Truth. Chat history is only a workbench.

## Generation routing

### V7 — ACTIVE

V7 replaces the previous mentor-style strategy-development line as the active research generation.

V7 is based on the user's earlier Kim Jikseon / Korean Traders Association study:
- Double-B (더블비),
- 더캔이지추격깨 context table,
- KTR session-range/risk framework.

The current V7 authority is **not an EA and not a validated strategy**.

V7 starts from a discretionary/contextual research contract:

```text
Double-B
= rare / abnormal event detector

Context
= direction and setup-type evidence

KTR
= session-relative distance / force unit

Trade plan
= event-specific Entry / WAIT / SKIP / SL / TP / optional staged entry
```

The central classification problem is:

```text
FRESH EXPANSION  -> BREAKOUT
RANGE EXTREME    -> BASIC
TERMINAL EXPANSION -> TURNING
INSUFFICIENT ASYMMETRY -> WAIT / SKIP
```

No single candle-close rule, Bollinger-side rule, or fixed KTR multiplier has direction authority.

### V6 — CLOSED

V6 mentor-style H/L1/L2 development is closed.

Final external/temporal evidence:
- Gold-family replication was only partial.
- 2026 factor-diverse holdout failed the combined frozen architecture.
- L2 remained the strongest portable finding.
- L1 failed to replicate.
- H showed multi-R payoff function but no validated positive edge.

V6 remains a historical research control and reproducibility asset only.
No further V6 strategy-semantic development is authorized by default.

Read:
`docs/ea/v6/V6_FINAL_VALIDATION_AND_CLOSE.md`.

## Current objective

Do **not** build a V7 EA yet.

The immediate objective is to determine whether the contextual distinctions discovered with hindsight can be made **causally, before future bars are visible**.

Priority:

1. preserve the 24 reverse-engineered Double-B events as consumed discovery only;
2. build a larger untouched Double-B event set;
3. hide all future bars at each event close;
4. record `ENTER_NOW / WAIT_CONFIRM / SKIP`;
5. classify `BASIC / BREAKOUT / TURNING / UNKNOWN`;
6. record natural-language evidence without forcing weak proxies;
7. record event-specific KTR-based SL/TP and staged-entry plan before revealing future;
8. reveal outcomes only after decisions are locked;
9. measure how much of the hindsight upper bound is causally recoverable;
10. only after repeatable blinded evidence exists, consider formalization or EA implementation.

## Permanent restrictions for current V7 phase

- no reuse of the same 24 hindsight events as validation;
- no converting hindsight event-specific KTR values into tuned global thresholds;
- no automatic `upper DB -> short` / `lower DB -> long`;
- no automatic `close outside both bands -> breakout`;
- no weak numerical proxy for a discretionary factor merely to fill the scorecard;
- no automatic 0.5-KTR averaging against every losing trade;
- no production claim from hindsight P/L;
- no mixing V6 H/L1/L2 conditions into V7 unless a future experiment explicitly preregisters the combination;
- no return to previous mentor-style strategy development by default.

