# EA Development Handoff

Status: `ACTIVE V7 ROUTER`
Date: `2026-08-30`
Expected base HEAD for this documentation update: `3c35cdc72b9f6046de716cd0d956a918021eba1e`
Active generation: `V7`
Current phase: `V7-003A GOLD25/BTC25 DOUBLE-B ANATOMY DISCOVERY`
Production authority: `NONE`
EA authority: `NONE`
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
11. Read `docs/ea/v7/V7_003A_GOLD25_BTC25_DEVELOPMENT_PLAN.md`.
12. Read `docs/ea/v7/DECISIONS_V7.md` and `BACKLOG_V7.md`.
13. Inspect exact raw data before doing any new research.

GitHub is the Single Source of Truth. Chat history is only a workbench.

## V7 current authority

V7 studies the user's Kim Jikseon-style:
- Double-B (더블비),
- 더캔이지추격깨 context framework,
- KTR session-distance/risk framework.

Role separation:

```text
Double-B = rare / abnormal event detector
Context = meaning, direction, archetype, timing evidence
KTR = session-relative distance / force coordinate system
Risk architecture = Entry / SL / TP / staged-entry exposure
```

Double-B itself has no LONG/SHORT authority.
Outside-band body close is evidence, not a breakout rule.
KTR has no universal SL/TP multiple.

## Current development universe

The first serious V7 development cohort is frozen as:

```text
GOLD#   — calendar year 2025
BTCUSD# — calendar year 2025
```

These are **development/discovery data**.

Future outcomes may be opened deliberately for reverse engineering.
Once opened, they are consumed and must never be cited as untouched V7 validation.

Do not expand the development universe because another market looks easier.

## Critical plan change

Do **not** start with blinded validation yet.

The method contains too many interacting discretionary elements and is not understood deeply enough.
The next phase is deliberate outcome-informed reverse engineering on GOLD25/BTC25.

```text
V7-003A  Double-B Anatomy
    ->
V7-003B  Context Atlas
    ->
V7-003C  KTR Geometry
    ->
V7-003D  Entry Architecture
    ->
V7-003E  Staging / Campaign Risk
    ->
V7-003F  Freeze a causal decision rubric
    ->
V7-004   Untouched blinded validation
```

Exact plan:
`docs/ea/v7/V7_003A_GOLD25_BTC25_DEVELOPMENT_PLAN.md`.

## Next-session first task

Begin with **V7-003A Double-B Anatomy**.

1. Verify exact full-year GOLD# 2025 and BTCUSD# 2025 raw M1 data.
2. Record file names, SHA256, coverage, timezone/server convention and spread fields.
3. Derive H1 from the M1 source using one frozen convention.
4. Detect **all** Double-B events using the frozen V7 band definition.
5. Freeze/save the complete event census before outcome subgroup analysis.
6. Build an anatomy ledger for every event.
7. Open the future because this is discovery.
8. Study recurring event families before designing a trading rule.

Do not begin with:
- trade P/L;
- KTR SL/TP optimization;
- staged entry;
- an additive scorecard;
- forcing every event into BASIC/BREAKOUT/TURNING.

The first deliverable is an **event anatomy atlas**, not a strategy backtest.

## Anatomy atlas questions

### Before the event
- prior 24–48 H1 state;
- trend / range / transition;
- move maturity;
- MA distance;
- causal support/resistance and remaining room;
- Bollinger compression/expansion;
- session context.

### Event candle
- upper / lower / ambiguous Double-B;
- body/full range/close location/wicks;
- size relative to KTR;
- BB20 geometry;
- BB4 geometry;
- BB20-vs-BB4 relationship;
- session opening-candle break/accept/reject state.

### After the event — discovery only
- 1h / 4h / 12h / 24h path;
- high/low excursion in KTR;
- time to ±0.5 / ±1 / ±2 / ±3 KTR;
- first structure acceptance/failure/reclaim;
- one-stage vs two-stage behavior;
- descriptive outcome family.

## Taxonomy rule

`BASIC / BREAKOUT / TURNING` are conceptual anchors but anatomy discovery must not force exactly three buckets.

Allowed descriptive families include:
- fresh breakout;
- failed breakout;
- range fade;
- climactic reversal;
- continuation -> turning;
- chaotic / no-edge.

## Context research priority

After anatomy:

1. session opening-candle break / acceptance / failure;
2. causal support / resistance;
3. Bollinger geometry and separation;
4. candle anatomy;
5. MA / trend maturity;
6. trendline only if meaningful information remains unexplained.

For each factor ask which job it helps:

```text
event meaning?
archetype?
direction?
entry timing?
SL invalidation?
TP / remaining room?
```

Do not promote a useful variable to every role.

## KTR boundary

KTR comes after event/context anatomy.

Ask:

```text
Where is structural invalidation?
How many current KTR is that?

Where is realistic destination / remaining room?
How many current KTR is that?

How does MAE/MFE geometry change when KTR is unusually small or large?
```

Structure decides the price level.
KTR interprets the distance.

## Entry / staging boundary

Entry architecture is studied only after event meaning and KTR geometry:

```text
IMMEDIATE
PLANNED_PULLBACK / ZONE
WAIT_CONFIRM
SKIP
```

Staged entry comes after a single-entry baseline and normal MAE by setup type.
The equal-risk-per-leg convention remains discovery-only and can create large campaign risk.

## Validation boundary

GOLD25/BTC25 are not validation.

Only after V7-003A~F freeze a causal decision process should V7-004 use a separate untouched cohort with future-hidden decisions.

GOLD 2021 remains untouched unless explicitly reallocated.

## V6 boundary

V6 mentor-style strategy development remains closed.
Do not import H/L1/L2 filters into V7 by default.
