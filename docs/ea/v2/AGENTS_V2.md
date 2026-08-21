# V2 Strategy Authority — Continuation Only

Status: `ACTIVE / CURRENT V2 STRATEGY AUTHORITY`
Effective date: `2026-08-22`
Fork source: `MentorDeterministicV1EA.mq5` at Git HEAD `123b41c880dbce2a17d560b4b7b081934d744700`
V1 status: `FROZEN / HISTORICAL CONTROL`
2021: `KEEP UNTOUCHED`

## 1. Authority boundary

This document governs only `mt5/experts/MentorDeterministicV2EA.mq5` and V2 research.

V1 code and V1 strategy documents remain frozen historical controls. V2 was forked from the validated V1 execution chain, but new V2 decisions are recorded here and in the V2 handoff/state documents rather than silently rewriting V1 history.

For V2, this document overrides V1 statements that grant first-position authority to `EXTERNAL_REVERSAL`. All other inherited baseline semantics remain unchanged until V2 explicitly supersedes them.

## 2. Active first-position scope

V2 has exactly one active first-position strategy scope:

```text
EXTERNAL_CONTINUATION
```

`EXTERNAL_REVERSAL` has no PLAN, Entry, pending-order, add-on, retry, or position authority in V2 on any symbol or timeframe.

Reversal-reference and reversal-permission state may remain inside inherited market-map infrastructure for diagnostics/history compatibility, but it cannot authorize a V2 scenario.

`INTERNAL_ROTATION` remains research-only and has no first-position order authority.

## 3. Continuation map authority

V2 keeps the inherited continuation hierarchy:

```text
H1 mature directional
-> H1 is highest active continuation map

H1 NEUTRAL / TRANSITION + M30 mature directional
-> M30 may be temporary highest active continuation map
```

A V2 trade must follow the current continuation direction of the active H1/M30 authority. Opposite-direction anticipation is not traded.

## 4. Inherited deterministic entry chain

Unless a later V2 decision explicitly changes it, the V2 control inherits:

```text
objective liquidity
-> H1/M30 continuation map
-> pre-existing eligible H1/M30/M15 Root OB
-> actual Root contact
-> valid Root-reaction sweep
-> meaningful M1 body CHoCH
-> fresh same causal-leg FVG
-> widest eligible FVG
-> first retest
-> Entry
-> normalized SL
-> frozen structural objective TP
```

Inherited control facts remain:

```text
ROOT_OB_DISTAL_20
LAST_OPPOSITE_OB + FVG_ORIGIN_OB
PD = reference only
same-entry Root merge
same-direction hedging add-ons allowed
opposite-direction coexistence blocked
no look-ahead
```

## 5. V2 control vs research modes

The V2 strategy-control profile is:

```text
scope = EXTERNAL_CONTINUATION only
regime = BASELINE_NO_REGIME_GATE
exit = ORIGINAL
EM = OFF
fixed risk money = $100 for standard research comparisons
```

`SMART_PARTIAL_V2` and `ENTRY_SURVIVAL_QUARANTINE_V2` are inherited research modes, not yet frozen V2 baseline authority.

They must remain independently switchable so V2 can separate:

```text
Entry edge
winner-management edge
loss-cluster / exposure-management edge
```

## 6. Current V2 research questions

V2 development is organized around three causal questions.

### A. Profit preservation without killing the tail

Once a trade proves itself, how much realized profit can be protected without cutting the rare multi-R winners that create expectancy?

Special focus:

```text
+2R reached
-> how far may price retrace before true large winners continue?
-> can a positive profit floor replace near-zero cost-BE?
```

Do not impose a fixed +2R -> +1R trail without measuring post-+2R retracement of actual large winners.

### B. Distinguish local +1R reactions from true continuation runners

At first +1R, distinguish:

```text
local reaction likely to exhaust near 1R
vs
state capable of 2R / 3R / structural-objective continuation
```

Current strongest evidence remains M30 protected-to-external maturity / remaining room at +1R. It is a winner-continuation variable, not an Entry gate.

### C. Genuine loss mechanism and solution

For trades that hit original SL before +1R, determine whether the failure came from:

```text
true directional / structural failure
local source failure while HTF continuation remains valid
same-Root timing / SL sensitivity
clustered failure of the Entry architecture
```

The goal is not to turn every loss into a winner. Solutions may include better causal completion, re-entry after a genuinely new source, probe/quarantine exposure management, or abandoning a failed premise. Static threshold mining remains prohibited.

## 7. Promotion standard

No V2 solution is promoted from one symbol-year.

Required evidence:

```text
realized WR >= 50%
average winner meaningfully > 1R
positive cost-adjusted expectancy
acceptable DD / loss streak
multiple years and markets
LONG/SHORT relation does not collapse
zero unresolved execution divergence in the evidence used
```

A market-specific rule may be retained only if explicitly classified as market-specific rather than silently generalized.
