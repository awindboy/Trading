# V9 Next Research Contract — EA R1 and Forward Demo

Date: `2026-09-14`
Status: `ACTIVE NEXT CONTRACT`

## Objective

Stop optimizing the historical prototype. Turn the current tick-native V9 prototype into a restart-safe, auditable MT5 EA and validate it prospectively on demo/forward data.

## Frozen market/strategy semantics

Do not retune during this contract:

- H1/H4 2-left / 2-right liquidity;
- tick-native H4 Arrival chronology;
- PRIMARY_ACTIVE / CHALLENGED resolver;
- nearest active opposite H1 structural SL;
- H4 ATR180 ERA scale;
- `ERA_RISK <= 4` eligibility;
- ANCHOR / CONTINUATION roles;
- ANCHOR exits at CHALLENGE_OPENS;
- CONTINUATION exits at next H4-liquidity Arrival;
- no fixed TP;
- no SHORT ban;
- no session/day/hour/duration filter.

## Required EA R1 gates

1. MetaEditor compile: zero errors.
2. Hedging-account requirement explicit.
3. Persistent state and restart recovery for Grammar, route, active levels, ATR180, open Children and pending close retries.
4. No duplicate Child after reconnect/restart.
5. Client-side structural-SL guard behavior explicitly tested across disconnect/reconnect.
6. Market-closed entry/exit handling preserved and logged.
7. Semantic reference, requested price, actual fill, spread, commission, swap, slippage and broker retcode logged.
8. Tick-native multiple-Arrival sequencing preserved.
9. Historical actual-tick ledger parity regression test retained.
10. Default real-money execution remains disabled.

## Forward-demo evidence to collect

- expected vs actual entry/exit slippage;
- spread distribution at authorization and exit;
- margin usage and rejected orders;
- partial fills if any;
- close-retry delay and gap cost;
- restart incidents;
- Anchor/Continuation concurrency;
- actual tick PnL by direction and role;
- live structural-risk distance and ERA_RISK;
- open-position mark-to-market drawdown.

## Money-management rule

No compounding risk policy is frozen in this contract.

Forward demo should begin with fixed small volume so market semantics and execution reliability are measured independently of leverage. Risk sizing can be promoted only after the execution layer is stable.

## Prohibited repair

Do not add a SHORT ban, weekday/session filter, duration stop, tighter ERA threshold, fixed TP, or new entry confirmation merely because a forward sequence loses.
