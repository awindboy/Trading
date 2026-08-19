# EA Development Handoff

Last updated: 2026-08-19
Repository base checked: 4798a0607f11946b7914ed7f804b193f03785711
Status: D-135A BUILD 1.91 LONG-RUN EXECUTION BASELINE VALIDATED / STRATEGY ROBUSTNESS RESEARCH STARTED
Current phase: semantic detector audit + regime/strategy robustness research
Remaining execution issue: recoverable broker pending-cancel rejection retry

## Authority

- `AGENTS.md` is the highest strategy authority.
- `docs/ea/EA_SPEC.md` defines the deterministic implementation contract.
- `docs/ea/DECISIONS.md` preserves important design decisions.
- `docs/ea/TEST_RESULTS*.md` preserves test evidence.
- This HANDOFF is intentionally a current-state document, not a historical phase archive.
- Historical implementation chronology should be recovered from DECISIONS, TEST_RESULTS, and Git history rather than duplicated here.

## Current baseline

The deterministic V1 pipeline is substantially complete and should be preserved as the control:

```text
H1/M30 map
→ eligible HTF Root OB
→ Root contact
→ direction-compatible M1 liquidity Sweep
→ later M1 protected-break CHoCH
→ causal fresh M1 FVG
→ widest eligible FVG
→ first retest Entry
→ contributor-merged SL/objective geometry
→ hedging same-direction execution
→ pending/fill/cancel/close reconciliation
```

Current research baseline:
- build `1.91`
- phase `D135A_CANCELED_PENDING_LIFECYCLE_HOTFIX`
- primary validation SL = `ROOT_OB_DISTAL_20`
- same-direction independent add-ons allowed on hedging accounts
- opposite-direction coexistence blocked
- FVG-origin OB and last-opposite OB both baseline Root recognizers
- PD Array remains context/reference only

Do not redesign this chain from memory. Read AGENTS/EA_SPEC/DECISIONS before changing strategy semantics.

## Long-run execution status

D-135A 2025 full-year real-tick regression passed the D-134 lifecycle target:

```text
execution geometry = 74
pending accepted = 73
pending canceled = 15
filled = 58
closed = 58
opposite-direction conflict = 1
execution divergence = 0
reported runtime ≈ 7m10s
D-134 runtime ≈ 9h
```

Entry/FVG/SL/TP and managed fill/close economics were equivalent to the D-134 baseline apart from non-strategic simultaneous ticket ordering.

Focused durable record:
`docs/ea/TEST_RESULTS_D135A_2023_2025.md`

## Remaining execution edge case

A multi-year D-135A run exposed one separate broker-safety problem:

```text
strategy pending cancellation required
→ broker cancel request rejected temporarily
→ example retcode 10018 / Market closed
→ build 1.91 does not retry later
→ canceled strategy order may remain live at broker
→ later fill can cause EXECUTION_DIVERGENCE
```

Observed fixture:

```text
2023-12-22 cancel rejected: Market closed
2024-01-05 previously canceled LONG pending filled
→ FILLED_AFTER_STRATEGY_CANCELLATION / execution divergence
```

Required future execution fix:
- keep the exact pending ticket managed after recoverable cancellation rejection;
- retain execution/divergence lock while unresolved;
- retry exact-ticket cancellation when broker conditions allow;
- terminalize only after broker cancel/fill proof.

This issue is separate from strategy-signal research. Multi-year profitability runs containing this divergence are research evidence only, not final profitability validation.

## Current strategy problem

The project is no longer blocked primarily by causal pipeline correctness.

The new question is whether the objects being detected are economically and visually meaningful.

Current concerns:

1. Structure/trend may be mechanically correct but not represent the market state a human trader would call meaningful.
2. Root OB recognition may select arbitrary-looking candles inside consolidation rather than a causal institutional-looking source.
3. Liquidity detection may promote stale, already-resolved, weak, or visually insignificant highs/lows.
4. The current H1/M30 "regime" is mainly directional authorization from structure ownership, not a true market-regime detector.
5. A causal Sweep → CHoCH → FVG chain cannot create edge if its upstream structure/liquidity/Root inputs are poor.

Long-run evidence is inconsistent across years, which makes ad-hoc optimization especially dangerous.

## Current research direction

Read next:
`docs/ea/STRATEGY_RESEARCH_STATE.md`

The immediate research objective is not to add filters.

First verify, visually and statistically, whether each upstream detector produces objects that are meaningful to a human chart reader:

```text
Structure / Trend
→ Liquidity
→ Root OB
→ Directional map / regime
→ Sweep
→ CHoCH
→ FVG
```

A TradingView visual-audit indicator is being developed for this purpose. It is an audit tool only, not strategy authority and not a parity proof.

The key conceptual correction is:

```text
bullish H1 structure != automatically bullish trading regime
bearish H1 structure != automatically bearish trading regime
```

The research target is not perfect Bull/Bear/Range prediction. It is to identify market states in which the existing setup has or lacks repeatable expectancy.

## Immediate next actions

1. Finish TradingView visual-audit indicator compile/runtime validation.
2. Inspect representative 2023, 2024, and 2025 windows without changing the EA.
3. Catalogue systematic detector mismatches:
   - meaningless wave/structure ownership,
   - weak/stale liquidity,
   - questionable Root OB,
   - late or misleading directional regime,
   - trivial Sweep/CHoCH.
4. Prefer blind or outcome-independent chart sampling where practical so winner/loser knowledge does not define the detector standard.
5. Decide whether the problem is upstream semantic detection or downstream trade construction.
6. Only after repeated cross-year evidence exists, design one minimal research variant at a time.
7. Separately close the recoverable pending-cancel retry edge case before using a multi-year run as final profitability evidence.

## Do not do yet

- Do not optimize thresholds from one bad year.
- Do not add arbitrary EMA/ADX/ATR/RSI filters just to repair the equity curve.
- Do not remove M30, SHORT, FVG-origin OB, add-ons, or other branches solely from one period.
- Do not introduce a generic quality score or RR score.
- Do not use ML/HMM/clustering before validating that the underlying structure/liquidity/Root labels are meaningful.
- Do not mix baseline semantics with multiple experimental switches.
- Do not interpret a causal implementation PASS as proof that the trading concept itself has edge.

## Working principle

The current research question is:

> Are we feeding a correctly implemented execution pipeline with the right market objects?

Preserve the deterministic baseline as the control. Challenge each upstream assumption before optimizing downstream trade parameters.
