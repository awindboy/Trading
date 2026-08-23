# V2 Development Handoff

Last updated: 2026-08-23  
Git HEAD at D154M package creation: `f5fef409cce86cfc1636d7b4f267cbd126b1979c`  
Current tested research base: `2.10R0L10 / D154K` with compact-log terminal sync  
Target research build: `2.11R0L11 / V2_D154M_EXECUTION_FRICTION_COUNTERFACTUAL`  
Current phase: **D154M COMPLETE / POST-FILL QUOTE FRICTION PARTIAL CAUSE / D154N NEXT**  
V1: **FROZEN HISTORICAL CONTROL**  
2021: **KEEP UNTOUCHED**

## Startup order for the next session

1. Check latest GitHub commit.
2. Read root `AGENTS.md`.
3. Read `docs/ea/v2/AGENTS_V2.md`.
4. Read root `docs/ea/HANDOFF.md`.
5. Read this file.
6. Read `docs/ea/v2/RESEARCH_SYNTHESIS_D154A_D154L.md`.
7. Read `docs/ea/v2/D154L_COST_SCALE_TRANSFER_VALIDATION_RESULTS.md`.
8. Read `docs/ea/v2/D154M_EXECUTION_FRICTION_COUNTERFACTUAL.md`.
9. Then inspect `RESEARCH_STATE_V2.md`, `BACKLOG_V2.md`, and current code.

GitHub remains the Single Source of Truth.

## Strategy authority

Unchanged:

```text
EXTERNAL_CONTINUATION only
BASELINE_NO_REGIME_GATE
ROOT_OB_DISTAL_20
LAST_OPPOSITE_OB + FVG_ORIGIN_OB
PD = reference only
same-entry Root merge
same-direction add-ons
opposite-direction coexistence blocked
no look-ahead
```

No D154A-L research result has changed baseline Entry authority.

## Current objective

Entry survival remains the main unresolved bottleneck.

2025:

```text
GOLD25    30/53  = 56.6%
BTC25     60/127 = 47.2%
SILVER25  18/46  = 39.1%
CADJPY25  30/113 = 26.5%
```

Keep Entry survival separate from +1R winner continuation and post+2R exit architecture.

## Research state in one page

Rejected / demoted as universal Entry rules:
- Fill-time M1 maturity;
- delayed same-direction INITIAL_BOS;
- fresh-FVG replacement Entry;
- post-SL new Root rescue;
- M1 TRANSITION-at-sweep veto;
- stale prior-owner Root;
- any same-owner BOS refresh cancellation;
- static H1/M30 alignment;
- post-contact same-direction HTF BOS veto;
- simple HTF protected-to-external exhaustion.

Supported but stage-limited:
- M30 maturity at +1R for winner continuation;
- V3E as provisional post+1R profit-preservation reference.

Strongest current cross-market Entry-survival mechanism:
- execution friction relative to causal M1 reaction scale.

D154K:
```text
GOLD25 spread/reactionTR = 0.342, survival 56.6%
CADJPY spread/reactionTR = 2.125, survival 26.5%
```

D154L 2025 transfer:
```text
GOLD   0.342 -> 56.6%
BTC    1.015 -> 47.2%
SILVER 1.701 -> 39.1%
CADJPY 2.125 -> 26.5%
```

Interpretation boundary:
- supported as cross-market transfer/viability mechanism;
- not supported as a per-trade spread filter;
- not sufficient to explain yearly GOLD regime changes.

## Immediate D154M question

Directly compare actual executable barrier outcome with an entry-side quote counterfactual.

```text
Actual:
LONG=BID
SHORT=ASK

Shadow:
LONG=ASK
SHORT=BID
```

Same actual Fill, original SL and +1R barriers.

Primary count:
```text
actual SL_FIRST -> shadow PLUS_1R
```

This is shadow-only and has no strategy authority.

## D154M execution order

```text
1. Apply D154M package.
2. Compile the exact runner-selected terminal MQ5; require 0 errors.
3. Run tools/verify_d154m_terminal_compile.py.
4. Run tools/run_d154m_friction_counterfactual.py.
5. Require GOLD/CADJPY Q1 OFF/ON canonical parity.
6. Analyze GOLD23/GOLD24/GOLD25/BTC25/SILVER25/CADJPY25 pair outcomes.
7. Do not design a spread threshold from the same results.
```

## Critical infrastructure note

The D154K session exposed a source/binary routing trap: `mt5_batch_runner.py` executes the EX5 discovered inside the selected MT5 AppData data directory. Repo MQ5 changes are not sufficient unless the exact runner-selected terminal source is compiled.

The D154M apply package therefore:
- discovers the exact runner terminal;
- copies the repo source beside the selected EX5;
- records pre-compile EX5 SHA;
- requires post-compile SHA change before the test.

Do not remove this safeguard.


## D154M completed / D154N next

D154M clean result:

```text
cell       actual WR   entry-side quote shadow WR   actual SL -> shadow +1R
GOLD23     52.3%       60.0%                        5
GOLD24     46.2%       48.1%                        1
GOLD25     56.6%       58.5%                        1
BTC25      47.2%       52.8%                        7
SILVER25   39.1%       39.1%                        0
CADJPY25   26.5%       41.6%                       17
```

There were zero impossible `ACTUAL_PLUS_1R_TO_SHADOW_SL` pairs and zero D154M integrity warnings.

Interpretation:
- executable exit-side quote friction is a real causal loss mechanism;
- it is large in CADJPY and material in BTC;
- it is absent in SILVER25 despite SILVER's high D154L cost scale;
- therefore D154L cost-scale remains a supported cross-market viability relation, but post-Fill quote-side disadvantage is only one component.

No strategy change.

Next phase is D154N: measure pending-placement -> opposite-quote first touch -> executable-quote Fill delay/depth. This tests whether spread makes actual Entry occur later/deeper after the structural price has already been reached on the non-entry quote.

If D154N does not explain the residual SILVER/CADJPY weakness, stop extending the execution-cost hypothesis and return to underlying market-regime / path-quality research.
