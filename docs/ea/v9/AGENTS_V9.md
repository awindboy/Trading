# V9 Research Instructions — Current Authority

Last synchronized: `2026-09-14`
Status: `ACTIVE / PROTOTYPE COMPLETE / ACTUAL-TICK VALIDATED / FORWARD-DEMO NEXT`
Production authority: `NONE`
EA authority: `RESEARCH / DEMO ONLY`
Market authority: `GOLD# ONLY`
Base GitHub HEAD before this sync packet: `60d95493a5607c0fc288eb4194505fa2c1a56656`
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
12. `docs/ea/v9/V9_NEXT_RESEARCH_CONTRACT_FORWARD_DEMO_20260914.md`
13. current EA/runtime/code state.

Older one-active-Child, hidden-gate, fixed-GOLD-SL, M1-only ambiguity, and pre-ERA4 documents remain historical evidence only when they conflict with the current prototype authority.

## 1. Data governance

By explicit user override, all supplied V9 GOLD# data are research-consumable. The old `2025-07 LOCKED` and `2021 untouched reserve` governance is superseded.

Current supplied authoritative M1 spans `2022-01-03 01:00` through `2026-08-28 23:57`. MT5 actual-tick validation continued through `2026-09-11 23:57:59` using broker tester history. No remaining supplied period is treated as hidden/OOS.

This does **not** permit hindsight repair: every replay must remain causal and stopped Children remain dead.

## 2. Current prototype in one block

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

Distinct H4 liquidity raids on distinct ticks are distinct Arrivals. M1 aggregation is no longer execution authority for intraminute ordering.

## 3. Current evidence hierarchy

1. Actual MT5 real-tick chronology and Bid/Ask fills for execution questions.
2. Authoritative raw M1 for long-span bar/object reconstruction and parity.
3. Uploaded H1/H4/M15/M5 only as parity/visual acceleration aids.
4. R-normalized results are secondary; fixed-size money/price PnL is the primary economic comparator unless a money-risk sizing policy is explicitly being studied.

## 4. Actual-tick status

Reference-period actual-tick run (`2022` through `2026-08-28`) produced `1,316` closed Children, `+5,028.62`, PF `1.425`, WR `60.18%` at fixed `0.01 lot`.

Full uploaded closed ledger through `2026-09-09` contains `1,322` closed Children, `+4,954.61`, PF `1.412`, WR `60.14%`; two Children remained open at tester end.

Actual tick validation confirmed that M1 ambiguity was materially optimistic: tick-collision cases were overwhelmingly adverse. It also revealed sequential multiple H4-liquidity Arrivals inside one M1 minute.

## 5. Money management status

Money management is **not frozen strategy authority**.

Canonical replay uses entry-time equity, actual executable entry-to-structural-SL distance, 0.01-lot steps, and the uploaded actual-tick PnL path.

- Full 2022-2026, 1% target from $1,000: realized `$5,876.54`, max realized balance DD `36.77%`; minimum-lot oversizing occurs on `80.66%` of entries.
- 2025-2026 only, 10% target per Child from $1,000: realized `$21,172.22`, marked equity `$21,852.95`, peak balance `$106,529.39`, max realized balance DD `85.47%`, max lot `2.76`.

Do not call the latter a safe 10% strategy: ANCHOR + CONTINUATION can overlap, producing near-20% combined planned structural exposure.

## 6. Permanent guardrails

- no future peek or hindsight trade insertion;
- stopped Child is dead;
- Parent/route and Child remain separate;
- Hard SL is fixed before entry and never widened;
- do not invent SHORT bans, session filters, duration filters, cooldowns, retry limits, trade quotas, forced side balance, or fixed TP from postmortem slices;
- tick chronology outranks M1 intraminute guesses;
- current prototype is research/demo authority, not production/live-capital authority.
