# V13 research instructions — LTF route state-machine generation

Last synchronized: `2026-09-29`
Status: `BASELINE 0 FROZEN / LTF ROUTE RECONSTRUCTION A ACTUAL-TICK VERIFIED / NOT PROMOTED`
Market authority: `GOLD# ONLY`
Base GitHub `main` checked: `1555d2b06b4dabdbadf14366c26e4f2177506463`

## 0. Resume order

1. repository `AGENTS.md`;
2. this file;
3. `V13_DOCUMENT_AUTHORITY_MAP_20260926.md`;
4. `V13_OBJECTIVE_AND_EVALUATION_UPDATE_20260928.md`;
5. `HANDOFF_V13.md`;
6. `RESEARCH_STATE_V13.md`;
7. `V13_BASELINE0_HA_MAX10_CONTRACT_20260926.md`;
8. historical HA-0..HA-8/X1/X2 contracts/receipts only when their evidence is
   needed;
9. `V13_FULL_RESEARCH_CHRONICLE_20260929.md` and
   `V13_LTF_BRANCH_DECISION_LOG_20260929.md`;
10. `V13_LTF_ROUTE_Q75_Q50_ACTION_CONTRACT_20260929.md`;
11. `results/V13_LTF_ROUTE_Q75_Q50_RESEARCH_RECEIPT_20260929.md`;
12. `V13_LTF_ROUTE_Q75_Q50_MQL5_VALIDATION_PROTOCOL_20260929.md` before tester work;
13. `results/V13_LTF_ROUTE_Q75_Q50_ACTUAL_TICK_REPLAY_RECEIPT_20260929.md`;
14. `mt5/experts/V13LTFRouteQ75Q50_PolicyReplayEA.mq5` before implementation changes;
15. HA-9 coverage and historical LTF checkpoints before reopening a rejected mechanism.

Later GitHub commits always outrank this package.

## 1. Baseline 0 remains frozen as comparator

Standard H4 HA formulas, Journey/color semantics, max-10 successful Child
entries and opposite-H4 close/reverse remain unchanged. Do not silently change
Baseline 0 when evaluating the current candidate.

## 2. Current strategy candidate: LTF route q75/q50

- Child #1 is unchanged Baseline 0.
- H4-timed add-ons are replaced by M30 correction / fresh M15 POI Children.
- Causally confirmed M30/H1 swing levels form the forward destination route.
- Strict-prior OOF hurdle EV q75 admits one fixed-size Child.
- First destination delivery is runtime proof, never a TP by itself.
- The first damaged post-delivery M30 correction uses a separate strict-prior
  OOF q50 repair decision.
- No q65/q70 rescue, score-based size increase, year exception or embedded
  retraining is authorized.

## 3. Revised research objective

The current goal is to make the **ordinary trade stream** less loss-heavy and
more consistently upward. The primary measurements are:

1. losing Child count/share;
2. non-flat win rate;
3. consecutive-loss length;
4. chronological trade-stream DD;
5. 10/25/50/100-trade block positive share and median P/L;
6. year slices;
7. P/L after removing the largest profitable Journeys.

Total net and PF are still reported. Right-tail sacrifice is a measured cost,
not an automatic rejection gate.

This supersedes earlier active-language such as “preserve the large continuation
tail” as a strategy objective. Historical receipts remain factual records.

## 4. Current evidence hierarchy

Causal M1/H4 audit, consumed 2024-01-01..2026-08-28:

```text
Baseline:  1,430 wins / 2,427 losses / 1 flat
           win rate 37.08%, net +8,147.11, PF 1.19995

HA-9:      2,151 wins / 1,685 losses / 22 flat
           win rate 56.07%, net +3,946.06, PF 1.17634

losses reduced: 742 (-30.6%)
trade-sequence max DD: 3,756.99 -> 1,283.65
max consecutive losses: 25 -> 14
```

HA-9 remains important historical evidence. SA-1 is the current actual-tick
reference: 1,783 trades, `+$2,791.87`, PF `1.215`, DD `$971.77`.

The original LTF session's exact q50 ledger remains absent. Reconstruction A
recovered the same 512 LTF / 1,477 combined population and passed exact
2,954-action actual-tick parity. It produced `+$4,461.37`, PF `1.301`, 554 wins,
922 losses, one flat, realized DD `$1,018.77`, exact-tick equity DD `$1,787.36`
and maximum loss streak 15.

Reconstruction A is **not promoted**. Relative to SA-1 it has better payoff and
net, but more losses, much lower win rate, longer streaks and greater exposure.
Do not describe the old session result as reproduced and do not convert this
replay harness into an embedded production EA on the consumed sample.

## 5. Causal boundaries

- Completed-bar inputs only for state, POI and swing construction.
- A pivot is invisible until its right-side confirmation bars complete.
- A consumed destination cannot be restored as an active target.
- First destination delivery cannot be converted into a hindsight entry or TP.
- No future H4/M1 may influence an earlier Child decision.
- No hindsight recovery after a Child is closed.

## 6. Next work

1. preserve Reconstruction A, its hashes and actual-tick receipt unchanged;
2. use a predeclared forward shadow period after `2026-08-28 20:00`, or freeze a
   genuinely new mechanism before observing its future result;
3. defer embedded-model and live-EA work until a candidate meets the active
   ordinary-equity objective;
4. in any later EA upgrade, replace closed-market retry storms with
   session-aware scheduling/backoff without backfilling expired entries.

Do not rescue Reconstruction A with q65/q70, fitted repair thresholds, sizing,
side/year exceptions or another pass over the consumed period.
