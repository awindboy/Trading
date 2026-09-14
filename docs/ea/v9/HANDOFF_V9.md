# V9 Development Handoff

Last updated: `2026-09-14`
Status: `PROTOTYPE COMPLETE / ACTUAL-TICK VALIDATED / FORWARD-DEMO NEXT`
Production authority: `NONE`
EA authority: `RESEARCH / DEMO ONLY`

## Resume point

Do not return to broad entry-feature mining. The V9 prototype is mechanically coherent enough to move into execution/runtime and forward-demo work.

Current chain:

```text
H4 liquidity Arrival / Delivery Grammar
+ causal H1 structural invalidation
+ ERA4 structural-risk eligibility
+ ANCHOR / CONTINUATION Child role split
+ tick-native Bid/Ask chronology
+ MT5 EA execution ledger
```

## Current prototype

- H1/H4 liquidity geometry: 2-left / 2-right.
- Entry authorization: causal PRIMARY_ACTIVE H4-liquidity Arrival.
- H1 Hard SL: nearest active opposite H1 swing liquidity.
- Era normalization: previous-completed H4 Wilder ATR180.
- Entry eligibility: `ERA_RISK <= 4`; do not clip the structural SL.
- First accepted Child in route: ANCHOR; exits at CHALLENGE_OPENS unless own SL first.
- Later accepted Children: CONTINUATION; exit at next H4-liquidity Arrival unless own SL first.
- No fixed TP.
- Tick chronology resolves M1 ambiguity.

## Actual-tick validation

MT5 real-tick tester run validated the prototype from 2022 onward.

Reference interval through `2026-08-28`:

```text
closed trades  1,316
wins              792
losses            524
WR               60.18%
PnL           +5,028.62
PF                1.425
```

Full uploaded closed ledger through September:

```text
closed trades  1,322
PnL           +4,954.61
PF                1.412
WR               60.14%
```

LONG remains the main economic engine; SHORT is near breakeven. This is evidence, not permission to ban SHORT.

## Important tick discoveries

1. H4-liquidity geometry itself matched the M1 reference minute/side/extreme on all 1,733 reference Arrival minutes.
2. Tick replay produced additional sequential Arrivals inside individual M1 minutes: 87 minutes had multiple H4-liquidity raids, up to 5 in one minute.
3. M1 `AMBIGUOUS` cases were mostly adverse when tick order was revealed; actual tick economics sit close to prior ambiguity-worst-case stress.
4. `market closed` caused 10 entry failures and 16 close failures; close retries succeeded later but gap risk is real.

## Money management

Keep fixed 0.01 lot as the primary strategy-validation baseline.

Sizing simulations are research only:

- Full-history $1,000 / 1% target: `$5,876.54`, DD `36.77%`, but 80.66% of entries cannot be reduced enough because 0.01 lot already exceeds 1% planned risk.
- 2025+ $1,000 / 10% per Child: `$21,172.22` realized, but DD `85.47%`; overlap makes combined planned exposure approach 20%.

Do not promote 10% sizing to live authority.

## Next work

Use `V9_NEXT_RESEARCH_CONTRACT_FORWARD_DEMO_20260914.md`.

Priority:

1. merge/compile the tick-native EA under the current prototype semantics;
2. freeze restart/state recovery and client-side structural-SL behavior;
3. forward-demo on a hedging account with event/trade logs retained;
4. measure real spread, slippage, rejected/partial fills, terminal disconnect/restart behavior, margin requirements, and session-close gaps;
5. only after stable demo evidence, decide a conservative capital-risk policy.
