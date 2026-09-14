# V9 Research Instructions — Current Authority

Last synchronized: `2026-09-15`
Status: `ACTIVE / PROTOTYPE FROZEN / ACTUAL-TICK VALIDATED / TERMINAL-STAGE SHADOW RESEARCH NEXT`
Production authority: `NONE`
EA authority: `RESEARCH / DEMO ONLY`
Market authority: `GOLD# ONLY`
Base GitHub HEAD for this update packet: `da0bf0592f1d5d447f224803182dec57fcf5d8b7`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`
Actual-tick event ledger SHA256: `c6e4a1117c1c0b8b073b09caaa433d940eae858dea1d9f9bc8c63fc95ab1c37c`
Actual-tick trade ledger SHA256: `bb4167b9c53ba3c73320f7dc032acc83f9d97bc6898aa04818947e167dc16bce`

## 0. Resume order

GitHub `awindboy/Trading` latest `main` HEAD remains the Single Source of Truth.
Read in this order:

1. `docs/ea/v9/AGENTS_V9.md`
2. `docs/ea/v9/V9_DOCUMENT_AUTHORITY_MAP_20260913.md`
3. `docs/ea/v9/HANDOFF_V9.md`
4. `docs/ea/v9/RESEARCH_STATE_V9.md`
5. `docs/ea/v9/V9_TRADING_MINDSET_AND_RESEARCH_GUARDRAILS_20260907.md`
6. `docs/ea/v9/V9_PROTOTYPE_AUTHORITY_20260914.md`
7. `docs/ea/v9/V9_MT5_ACTUAL_TICK_VALIDATION_20260914.md`
8. `docs/ea/v9/V9_MONEY_MANAGEMENT_STUDY_20260914.md`
9. `docs/ea/v9/V9_ACTUAL_TICK_EXECUTION_AND_ERA_SCALE_ADDENDUM_20260914.md`
10. `docs/ea/v9/V9_CAUSAL_NUMERIC_ANALYSIS_AND_TOOLING_PROTOCOL_20260910.md`
11. `docs/ea/v9/V9_DUAL_CLOCK_SEMANTIC_RUNTIME_ADDENDUM_20260912.md`
12. `docs/ea/v9/V9_TERMINAL_STAGE_HEIKIN_ASHI_RESEARCH_CHECKPOINT_20260915.md`
13. `docs/ea/v9/V9_NEXT_RESEARCH_CONTRACT_TERMINAL_STAGE_CAUSAL_DETECTION_20260915.md`
14. `docs/ea/v9/V9_NEXT_RESEARCH_CONTRACT_FORWARD_DEMO_20260914.md`
15. current EA/runtime/code state.

Older one-active-Child, hidden-gate, fixed-GOLD-SL, M1-only ambiguity, and pre-ERA4 documents remain historical evidence only when they conflict with current prototype authority.

## 1. Current prototype authority remains unchanged

```text
H1/H4 swing liquidity: causal 2-left / 2-right
H4 liquidity raid: tick-native Bid chronology
Grammar: PRIMARY_ACTIVE / CHALLENGED
Entry: immediate eligible PRIMARY_ACTIVE Arrival
Hard SL: nearest active causal opposite H1 swing liquidity
ERA_SCALE: previous completed H4 Wilder ATR180
ERA_RISK: abs(entry - structural SL) / ERA_SCALE
Eligibility: ERA_RISK <= 4

First accepted Child in active route = ANCHOR_CHILD
  -> own structural SL
  -> hold same-side H4-liquidity Arrivals
  -> exit at CHALLENGE_OPENS

Later accepted Child in same route = CONTINUATION_CHILD
  -> own structural SL
  -> exit at first subsequent H4-liquidity Arrival

No fixed TP.
No SHORT ban.
No Child-count cap.
No day/session/hour filter.
No duration timeout.
```

The 2026-09-15 Heikin-Ashi work is **shadow research only**. It does not replace any current exit authority.

## 2. Latest shadow research finding

The strongest new finding is not `HA1 is an exit rule`.
It is:

```text
HA signal quality depends strongly on when HA monitoring is activated.
```

If H4 Heikin-Ashi is monitored from Anchor entry, opposite-color HA frequently cuts normal pullbacks inside large multi-Child journeys and materially reduces the right tail.

A hindsight oracle experiment then activated HA only after the **true last accepted Child of the route**. This is future information and therefore cannot be used live, but it measures an upper bound for the activation-timing idea.

On the deterministic role-based M1 population of `1,139` resolved Children:

```text
BASE role policy
PnL +8,530.74 / PF 2.023 / WR 65.58% / DD 440.35

oracle LAST-CHILD -> HA1 -> close all still-open Children
PnL +13,863.22 / PF 3.475 / WR 70.41% / DD 288.75

oracle LAST-CHILD -> HA2 -> close all still-open Children
PnL +12,102.57 / PF 2.853 / WR 68.83% / DD 289.85
```

This is `HINDSIGHT ORACLE / UPPER BOUND ONLY`, not strategy evidence eligible for direct promotion.

## 3. Current strategy-research question

The next strategy-research problem is now:

> Can V9 recognize, using only causally known information, that the active route has entered a terminal-participation stage in which no further accepted Child is likely to be earned, so that H4 HA can be armed as a profit-protection event without cutting normal mid-journey pullbacks?

Do **not** turn this into a fitted Child-count rule such as `third Child`, `fourth Child`, `after N hours`, or similar.

Candidate causal information may include:

- remaining same-side H4 liquidity distance normalized by previous-completed H4 ATR180;
- opposite-side H4 liquidity distance and topology;
- active H4 liquidity counts and ages;
- route-relative movement-capacity change;
- Anchor MFE / giveback / realized expansion in ATR180 coordinates;
- H1 completed-bar state and volatility/range summaries;
- current accepted-Child/position state as descriptive context, not an optimized count threshold.

The target and evaluation must remain route-sequential. Checkpoint AUC alone is insufficient: the final test is whether an armed HA policy improves the chronological route/trade ledger without destroying the right tail.

## 4. Data governance

By explicit user override, all supplied V9 GOLD# periods are research-consumable. No supplied period remains hidden/OOS.

This does **not** permit hindsight repair. Every causal replay must use only information known at the decision point. The last-Child oracle is permitted only as a labeled upper-bound diagnostic and must never be presented as a causal strategy result.

## 5. Evidence hierarchy

1. MT5 actual real-tick chronology and Bid/Ask fills for execution questions.
2. Authoritative raw M1 for long-span bar/object reconstruction and parity.
3. Uploaded H1/H4/M15/M5 only as parity/visual acceleration aids after their bars are fully known.
4. Consumed-data shadow/oracle studies may define research targets but cannot change current strategy authority by themselves.

## 6. Permanent guardrails

- no future peek or hindsight trade insertion;
- stopped Child is dead;
- Parent/route and Child remain separate;
- Hard SL is fixed before entry and never widened;
- do not invent SHORT bans, session filters, duration filters, cooldowns, retry limits, trade quotas, fixed TP, or forced side balance;
- do not promote `last Child` itself, Child-count thresholds, or oracle activation timestamps into live rules;
- do not interpret HA opposite color as objective trend end;
- tick chronology outranks M1 intraminute guesses;
- current prototype remains research/demo authority, not production/live-capital authority.
