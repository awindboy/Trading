# V9 Development Handoff

Last updated: `2026-09-07`
Status: `ACTIVE V9`
Current phase: `DECISION CORRIDOR ENTRY CONTROL -> H4-NORMALIZED EXIT/DISTANCE -> SEQUENTIAL CONTINUATION / OPEN-ROUTE SHADOW RESEARCH`
Production authority: `NONE`
EA authority: `NONE`
Market: `GOLD# ONLY`
Untouched reserve: `GOLD# 2021`
Expected Git base for this update: `0880cafaac8752e2976ca970244dab6a215955d9`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`

## 1. Resume order

Every V9 session must:

1. refresh latest GitHub HEAD;
2. read `docs/ea/v9/AGENTS_V9.md`;
3. read this file;
4. read `docs/ea/v9/RESEARCH_STATE_V9.md`;
5. read `docs/ea/v9/V9_MANUAL_CHART_REPLAY_MARKET_MEMORY_AND_DECISIONS_20260907.md`;
6. read `docs/ea/v9/DECISIONS_V9.md`;
7. read `docs/ea/v9/DECISIONS_V9_ADDENDUM_20260907.md`;
8. read `docs/ea/v9/V9_PAPER_TRADING_JOURNAL_20260907.md`;
9. read `docs/ea/v9/V9_NEXT_RESEARCH_CONTRACT_EXIT_DISTANCE_OPEN_ROUTE_20260907.md`;
10. use the latest relevant result documents under `docs/ea/v9/results/`;
11. use V8 only as preserved upstream evidence/controls where V9 explicitly needs it;
12. inspect raw data before any new replay.

GitHub is the Single Source of Truth. Chat history is a workbench.

---

## 2. Why V9 exists

Permanent distinction:

```text
market understanding
!=
direction prediction
!=
good trade
```

V9 asks whether incomplete but causally disciplined market understanding can find trades where:

```text
wrong thesis -> observable relatively nearby
right thesis -> meaningful structural route
```

The working object remains the `Decision Corridor`:

```text
Falsification Anchor
        ^
        |
   Current Price
        |
        | open route
        v
Next Active Memory / Open Route
```

No V9 EA or production strategy exists.

---

## 3. Stable market-reading principles retained

Retain:

```text
Role > Pattern
boundary crossing != value translation
reaction != rejection
destination != reversal
direction correctness != trade quality
later same-direction movement cannot rescue an invalidated thesis
abrupt traversal != automatic continuation
```

Also retain:

- adaptive M5 -> M15 -> H1 -> H4 -> D1 history compression;
- sparse active memory;
- parent/child hierarchy;
- counterfactual thesis dependence;
- failed repair as a process hypothesis, not a pattern rule;
- NO TRADE / NOT YET as successful decisions;
- manage thesis, not unrealized P/L.

---

## 4. January 2026 discretionary development replay

Evidence class: `DISCRETIONARY / CONTAMINATED DEVELOPMENT`, not OOS validation.

Trades recorded:

| Trade | Direction | Entry | Structural outcome | Descriptive result |
|---|---|---:|---|---:|
| V9-PAPER-001 | SHORT | ~4445.70 | destination resolved | +1.52R |
| V9-PAPER-002 | LONG | ~4609.72 | destination resolved | +1.36R |
| V9-PAPER-003 | SHORT | ~4593.66 | destination resolved | +2.29R |
| V9-PAPER-004 | LONG | ~4605.77 | destination resolved | +1.95R |
| V9-PAPER-005 | LONG | ~4603.78 | destination resolved | +1.84R |
| V9-PAPER-006 | SHORT | ~4589.27 | weekend-gap / execution-censored failure | ~-3.36R first-print mark only |
| V9-PAPER-007 | SHORT | ~5512.62 | destination resolved | +1.42R |

Six destination-resolved examples sum to ~`+10.38R` descriptively. Do not report a validated WR/PF/expectancy. PAPER-006 has no exact executable loss because the structural invalidation was crossed during market closure.

Important lessons:

- waiting for repair can improve entry geometry;
- memory role can invert after genuine restoration;
- `touch/penetration != genuine restoration`;
- structural falsification can be close while executable gap risk is not;
- large parent scars can become tradeable only after smaller child repair creates a nearer counterfactual anchor;
- price discovery produced many obvious directional moves that the original known-destination contract could not trade.

Detailed replay: `results/V9_CAUSAL_REPLAY_202601.md`.

---

## 5. January 2025 period-transfer replay

Evidence class: `PERIOD-TRANSFER DEVELOPMENT / NOT UNTOUCHED OOS`.

Full January was replayed with the same qualitative V9 contract.

Result:

```text
actual trades: 1
2025JAN-PAPER-001 LONG
entry ~2653.74
falsification ~2649-2650 genuine re-loss
first destination ~2660-2663
exit ~2649.32
descriptive result ~-1.04R
```

The market later rallied above the original destination. This does not rescue the invalidated trade; the later rise is a new episode.

Dominant environment:

- balance / node-internal travel;
- direction becoming clear only after the first bridge was mostly consumed;
- frequent nearby active memories;
- price discovery without a known destination;
- substantially fewer tradeable Decision Corridors than January 2026.

Key conclusion:

> market-reading discipline transferred better than trade production/performance.

Do not call V9 period-robust yet.

Detailed replay: `results/V9_CAUSAL_REPLAY_202501.md`.

---

## 6. Deep January review

The 2025/2026 comparison supports:

- `direction correctness != trade quality` across both periods;
- causal hygiene around invalidation and later same-direction moves;
- structural role-change / repair as promising discretionary information.

It also exposes unresolved risks:

1. `genuine restoration` is still subjective;
2. `active vs consumed memory` can change room/destination selection materially;
3. parent context may be partly narrative unless its actual decision effect is recorded;
4. price discovery is a real blind spot of the original corridor;
5. execution continuity must be separate from structural risk;
6. 2026 results are strongly contamination-sensitive.

See `results/V9_JAN_2025_2026_DEEP_REVIEW_20260907.md`.

---

## 7. Distance architecture correction — H4 ATR coordinate

V8 evidence established that fixed-point movement has unstable meaning across volatility regimes. V9 now uses the same slow coordinate for research:

```text
S(t) = Wilder ATR14 of the immediately previous fully completed H4 bar
```

`S` is a coordinate system, not the thesis, SL, TP, or entry gate.

For every candidate record:

```text
Risk/S
FirstCheckpoint/S
nearest intervening memory/S
later route distances/S when relevant
```

Exact reconstructed S values for the January trades are documented in the Exit/Distance audit.

The completed 2026 winners generally reached CP1 after only about `0.29-0.44S`; their strong R came mainly from close structural invalidation rather than capturing a large fraction of the volatility episode.

Therefore:

```text
high R != large market-scale winner
```

---

## 8. Exit architecture shadow audit

Control A:

```text
100% exit at first natural destination / CP1
```

Neutral challenger C:

```text
50% exit at CP1
50% remain under original structural management
```

Same five CP1-reached audit rows:

```text
A sum  = +8.861R
C sum  = +4.758R
C - A  = -4.104R
```

C is therefore downgraded. Do not tune the partial ratio to rescue it.

Crucial finding:

```text
large favorable MFE existed after CP1
!=
slow structural runner captured it
```

The core exit problem is now `capture latency`: continuation/rejection may only become obvious after much of the favorable excursion has been given back.

Keep CP1 full-exit as the current comparison control, not as final production authority.

See `results/V9_EXIT_DISTANCE_SHADOW_AUDIT_20260907.md`.

---

## 9. Revised continuation research

Do not solve the problem by simply widening TP or holding a passive runner.

Primary challenger becomes:

```text
bridge 1 reaches CP1
-> original trade resolves / control exits
-> observe whether CP1 is actually consumed
-> wait for a NEW thesis-dependent falsification
-> verify intervening memory / room in H4 ATR coordinates
-> take a NEW continuation trade only if a new Decision Corridor exists
```

This preserves the best original entry's realized profit while allowing large winners to emerge as sequential bridges.

`consumed memory` alone is not enough for a re-entry.

---

## 10. Open-route / price-discovery research

Original V9 often treated:

```text
no known destination -> NO TRADE
```

This is now downgraded.

New descriptive state:

```text
last meaningful directional memory consumed
+
full causal history checked
+
no meaningful overhead/downstream active memory
=
OPEN ROUTE / PRICE DISCOVERY
```

But:

```text
PRICE DISCOVERY != TRADE
```

A trade still requires:

- no breakout chase;
- a pullback/repair or otherwise earned local structure;
- a nearby **thesis-dependent** falsification anchor;
- H4-normalized risk/room documentation;
- no fabricated micro-anchor merely to improve R.

Strong archaeology example: 2026-01-20 after ~4690 consumption. A 07:15 pullback remained above the consumed memory, giving a reconstructed risk of only ~`0.193S` before a major continuation.

Weak-geometry counterexample: 2025-01-30 after ~2785 consumption; using the genuinely thesis-dependent old boundary gave ~`0.699S` risk despite later upside.

These are development archaeology examples only. Seek negative open-route examples deliberately.

---

## 11. Current immediate research contract

Read `V9_NEXT_RESEARCH_CONTRACT_EXIT_DISTANCE_OPEN_ROUTE_20260907.md` before doing new replay.

The immediate work is:

1. keep original V9 entry logic as control;
2. use previous-completed H4 ATR14 for distance descriptions;
3. retain CP1 full exit as Exit Control A;
4. do **not** promote the 50/50 runner;
5. study `exit -> earned continuation re-entry` as the main continuation challenger;
6. open `OPEN ROUTE` as a separate discretionary research family;
7. prerecord what exactly counts as genuine restoration/invalidation;
8. record what parent context actually changes;
9. seek losses, failed consumption, false open routes, and bad re-entries deliberately;
10. keep GOLD# 2021 locked.

---

## 12. Formalization gate remains closed

Do not code a V9 strategy or EA until:

- more independent discretionary wins/losses/no-trades exist;
- open-route negatives exist;
- restoration and memory-consumption language is reproducible across sessions;
- another AI/session can identify substantially similar anchors/CPs from hidden-future charts;
- exit/re-entry semantics stop changing after each small sample.

Production status: `NONE`.
